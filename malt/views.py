from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, Paginator
from django.db import models, transaction
from django.http import HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin, BaseDetailView

from beer import public_storage
from beer.utils import collapse

from .models import PowerUser, FolderAsset, FileAsset
from .forms import UserForm, AssetAddForm, AssetMoveForm, YeastForm
from .caches import power_cache, member_cache
from .brewing import BrewError
from .brewery import Brewery
from .yeasts import CalendarYeast

User = get_user_model()


PAGE_SIZE = 50

CSRF_KEY = 'csrfmiddlewaretoken'


class UserIsSuperMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserIsPowerMixin(UserPassesTestMixin):
    def test_func(self):
        return power_cache.get(self.request.user)


class UserIsOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.is_owned()


class UserIsMemberMixin(UserIsOwnerMixin):
    pass


class AssetMixin:
    Asset = FolderAsset

    def get_objects(self, path):
        if path:
            names = path.split('/')
            parent = None
            for name in names[:-1]:
                parent = get_object_or_404(FolderAsset, user=self.request.user, parent=parent, name=name, trashed=False)
            asset = get_object_or_404(self.Asset, user=self.request.user, parent=parent, name=names[-1], trashed=False)
        else:
            names = []
            asset = None
        return names, asset


class AssetPathMixin:
    def get_url(self, names):
        if names:
            return reverse('asset_manage_folder', kwargs={'path': '/'.join(names)})
        else:
            return reverse('asset_manage')


class MaltMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['debug'] = settings.TEMPLATE_DEBUG
        context['power'] = power_cache.get(self.request.user)
        return context


class TemplateView(MaltMixin, generic.TemplateView):
    pass


class FormView(MaltMixin, generic.FormView):
    pass


class UserViewMixin(LoginRequiredMixin, UserIsSuperMixin):
    def get_suffix(self):
        if self.request.GET:
            return '?' + self.request.GET.urlencode()
        else:
            return ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suffix'] = self.get_suffix()
        return context

    def get_success_url(self):
        return reverse('user_manage') + self.get_suffix()


class UserManageView(UserViewMixin, FormView):
    form_class = UserForm
    template_name = 'malt/user/manage.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        promote = form.cleaned_data['promote']
        for username, defaults in form.users.items():
            user, created = User.objects.update_or_create(username=username, defaults=defaults)
            if not created:
                power_cache.set(user, promote)
            if promote:
                PowerUser.objects.get_or_create(user=user)
            else:
                PowerUser.objects.filter(user=user).delete()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            filter = collapse(self.request.GET['filter'])
        except KeyError:
            filter = ''
        if filter:
            users = User.objects.filter(username__icontains=filter).order_by('username')
        else:
            users = User.objects.all().order_by('username')
        paginator = Paginator(users, PAGE_SIZE)
        try:
            number = int(self.request.GET['page'])
            users = paginator.page(number)
        except (KeyError, ValueError, EmptyPage):
            users = paginator.page(1)
        users.power_pks = PowerUser.objects.filter(user__in=users).values_list('user', flat=True)
        context['filter'] = filter
        context['users'] = users
        context['focus'] = True
        return context


class SingleUserViewMixin(UserViewMixin, MaltMixin):
    model = User


class FormUserViewMixin(SingleUserViewMixin):
    fields = ['username', 'email', 'first_name', 'last_name']


class UserAddView(FormUserViewMixin, generic.edit.CreateView):
    template_name = 'malt/user/add.html'


class UserEditView(FormUserViewMixin, generic.edit.UpdateView):
    template_name = 'malt/user/edit.html'


class UserRemoveView(SingleUserViewMixin, generic.edit.DeleteView):
    template_name = 'malt/user/remove.html'


class UserChangeView(SingleUserViewMixin, TemplateResponseMixin, BaseDetailView):
    def post(self, request, *args, **kwargs):
        user = self.get_object()
        power_cache.set(user, self.promote)
        self.change(user)
        return redirect(self.get_success_url())


class UserPromoteView(UserChangeView):
    promote = True
    template_name = 'malt/user/promote.html'

    def change(self, user):
        PowerUser.objects.get_or_create(user=user)


class UserDemoteView(UserChangeView):
    promote = False
    template_name = 'malt/user/demote.html'

    def change(self, user):
        PowerUser.objects.filter(user=user).delete()


class UploadMixin(LoginRequiredMixin, UserIsPowerMixin):
    pass


class UploadManageView(UploadMixin, AssetMixin, generic.View):
    def post(self, request, *args, **kwargs):
        body = request.POST.dict()

        try:
            method = collapse(body.pop('method'))
            name = collapse(body.pop('name'))
        except KeyError:
            return HttpResponseBadRequest()

        if method == 'code':
            body['action'] = reverse('upload_code')
            return JsonResponse(body)

        if method == 'asset':
            if not name:
                return HttpResponseBadRequest('This field is required.')
            for validator in FileAsset.name.field.validators:
                try:
                    validator(name)
                except ValidationError as error:
                   return HttpResponseBadRequest(error)

            try:
                path = collapse(body['path'])
            except KeyError:
                return HttpResponseBadRequest()

            _, parent = self.get_objects(path)

            try:
                asset = FileAsset.objects.get(user=request.user, parent=parent, name=name, trashed=False)
            except FileAsset.DoesNotExist:
                asset = FileAsset.objects.create(user=request.user, parent=parent, name=name)

            key = asset.key()
            redirect_url = '{}://{}{}'.format(request.scheme, request.get_host(), reverse('upload_asset_confirm'))

            body = public_storage.post(key, redirect_url)

            try:
                body[CSRF_KEY] = request.POST[CSRF_KEY]
            except KeyError:
                pass
            return JsonResponse(body)

        return HttpResponseNotFound()


class UploadCodeView(UploadMixin, MaltMixin, TemplateResponseMixin, ContextMixin, generic.View):
    template_name = 'malt/error.html'

    def post(self, request, *args, **kwargs):
        brewery = Brewery(request.user, [])

        files = request.FILES
        if request.skip:
            files = None

        meta = request.POST.dict()
        try:
            del meta[CSRF_KEY]
        except KeyError:
            pass

        try:
            url = brewery.brew(files, meta)
        except BrewError as error:
            context = self.get_context_data(**kwargs)
            context['error'] = error
            return self.render_to_response(context)

        return redirect(url)


class UploadAssetView(UploadMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if settings.CONTAINED:
            return HttpResponseNotFound()

        try:
            key = collapse(request.POST['key'])
            url = collapse(request.POST['success_action_redirect'])
        except KeyError:
            return HttpResponseBadRequest()

        if not key:
            return HttpResponseBadRequest()

        if not url.startswith('http://'):
            return HttpResponseBadRequest()

        files = request.FILES

        if request.skip:
            return HttpResponseBadRequest()

        if len(files) != 1:
            return HttpResponseBadRequest()

        try:
            file = files['file']
        except KeyError:
            return HttpResponseBadRequest()

        public_storage.save(key, file)

        return redirect('{}?{}'.format(url, urlencode({'key': key}, safe='/')))


class UploadAssetConfirmView(UploadMixin, AssetPathMixin, generic.View):
    def get(self, request, *args, **kwargs):
        try:
            key = collapse(request.GET['key'])
        except KeyError:
            return HttpResponseBadRequest()

        paths = key.split('/')

        asset = get_object_or_404(FileAsset, user=request.user, uid=paths[-1])

        if not asset.active and public_storage.exists(asset.key()):
            asset.active = True
            asset.save()

        return redirect(self.get_url(asset.names()))


class PowerMixin(LoginRequiredMixin, UserIsPowerMixin):
    pass


class AssetViewMixin(PowerMixin, AssetMixin, AssetPathMixin):
    objects = None

    def get_objects(self):
        if self.objects is None:
            self.objects = super().get_objects(self.kwargs['path'])
        return self.objects


class AssetFormView(AssetViewMixin, FormView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        names, asset = self.get_objects()
        kwargs['Asset'] = self.Asset
        kwargs['user'] = self.request.user
        kwargs['names'] = names
        self.update(kwargs, asset)
        return kwargs


class AssetFilterMixin:
    def get_filter(self, Asset, **kwargs):
        return Asset.objects.filter(**kwargs).order_by('name')


class AssetManageView(AssetFilterMixin, AssetFormView):
    form_class = AssetAddForm
    template_name = 'malt/asset/manage.html'

    def update(self, kwargs, asset):
        kwargs['parent'] = asset

    def form_valid(self, form):
        FolderAsset.objects.create(user=form.user, parent=form.parent, name=form.name)
        return redirect(self.get_url(form.names))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        names, asset = self.get_objects()
        if names:
            context['name'] = names.pop()
            context['parent_url'] = self.get_url(names)
        else:
            context['name'] = 'assets'
            context['parent_url'] = None
        context['prefix'] = self.kwargs['path']
        context['folders'] = self.get_filter(FolderAsset, user=self.request.user, parent=asset, trashed=False)
        context['files'] = self.get_filter(FileAsset, user=self.request.user, parent=asset, trashed=False)
        context['focus'] = True
        return context


class AssetOverwriteMixin:
    def overwrite(self, user, source, target, is_file):
        if is_file:
            target.uid = source.uid
            target.active = source.active
            target.save()
        else:
            self.merge(user, source, target, False)
            self.merge(user, source, target, True)
        source.delete()

    def merge(self, user, source, target, is_file):
        if is_file:
            Asset = FileAsset
        else:
            Asset = FolderAsset
        for source_child in Asset.objects.filter(user=user, parent=source):
            if source_child.trashed:
                source_child.parent = target
                source_child.save()
            else:
                try:
                    target_child = Asset.objects.get(user=user, parent=target, name=source_child.name, trashed=False)
                except Asset.DoesNotExist:
                    source_child.parent = target
                    source_child.save()
                else:
                    self.overwrite(user, source_child, target_child, is_file)


class AssetFileMixin:
    Asset = FileAsset


class AssetMoveView(AssetOverwriteMixin, AssetFormView):
    form_class = AssetMoveForm
    template_name = 'malt/asset/move.html'

    def redirect(self, names):
        return redirect(self.get_url(names[:-1]))

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        is_file = self.Asset is FileAsset

        if 'overwrite' in request.POST:
            names, source = self.get_objects()
            target = get_object_or_404(self.Asset, pk=request.POST['pk'])
            self.overwrite(request.user, source, target, is_file)
            return self.redirect(names)
        else:
            form = self.get_form()

            if form.is_valid():
                if form.parent == form.asset.parent and form.name == form.asset.name:
                    return self.redirect(form.names)

                try:
                    asset = self.Asset.objects.get(user=form.user, parent=form.parent, name=form.name, trashed=False)
                except self.Asset.DoesNotExist:
                    form.asset.parent = form.parent
                    form.asset.name = form.name
                    form.asset.save()
                    return self.redirect(form.names)

                context = self.get_context_data(**kwargs)
                context['is_file'] = is_file
                context['path'] = form.path
                context['pk'] = asset.pk
                return TemplateResponse(request=request, template=['malt/asset/move_confirm.html'], context=context, using=self.template_engine)
            else:
                return self.form_invalid(form)

    def update(self, kwargs, asset):
        kwargs['asset'] = asset
        kwargs['initial']['path'] = self.kwargs['path']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        names = self.kwargs['path'].split('/')
        context['name'] = names.pop()
        context['parent_url'] = self.get_url(names)
        if names:
            context['parent_name'] = names.pop()
            context['grandparent_url'] = self.get_url(names)
        else:
            context['parent_name'] = 'assets'
            context['grandparent_url'] = None
        return context


class AssetMoveFileView(AssetFileMixin, AssetMoveView):
    pass


class AssetTrashView(AssetViewMixin, generic.View):
    def post(self, request, *args, **kwargs):
        names, asset = self.get_objects()
        asset.trashed = True
        asset.save()
        return redirect(self.get_url(names[:-1]))


class AssetTrashFileView(AssetFileMixin, AssetTrashView):
    pass


class AssetRecycleView(AssetFilterMixin, PowerMixin, TemplateView):
    template_name = 'malt/asset/recycle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folders'] = self.get_filter(FolderAsset, user=self.request.user, trashed=True)
        context['files'] = self.get_filter(FileAsset, user=self.request.user, trashed=True)
        return context


class AssetChangeMixin(PowerMixin, MaltMixin):
    model = FolderAsset

    def get_success_url(self):
        return reverse('asset_recycle')


class AssetChangeFileMixin:
    model = FileAsset


class AssetRestoreView(AssetChangeMixin, AssetOverwriteMixin, TemplateResponseMixin, SingleObjectMixin, generic.View):
    template_name = 'malt/asset/restore.html'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        names = self.object.names()
        parent = None
        for name in names:
            try:
                parent = FolderAsset.objects.get(user=request.user, parent=parent, name=name, trashed=False)
            except FolderAsset.DoesNotExist:
                parent = FolderAsset.objects.create(user=request.user, parent=parent, name=name)

        try:
            object = self.model.objects.get(user=request.user, parent=parent, name=self.object.name, trashed=False)
        except self.model.DoesNotExist:
            self.object.parent = parent
            self.object.trashed = False
            self.object.save()
            return redirect(self.get_success_url())

        is_file = self.Asset is FileAsset

        if 'overwrite' in request.POST:
            self.overwrite(request.user, self.object, object, is_file)
            return redirect(self.get_success_url())

        context = self.get_context_data(**kwargs)
        context['is_file'] = is_file
        context['path'] = '/'.join([*names, self.object.name])
        return self.render_to_response(context)


class AssetRestoreFileView(AssetChangeFileMixin, AssetRestoreView):
    pass


class AssetRemoveView(AssetChangeMixin, generic.edit.DeleteView):
    template_name = 'malt/asset/remove.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.get_object()
        context['path'] = '/'.join([*object.names(), object.name])
        return context


class AssetRemoveFileView(AssetChangeFileMixin, AssetRemoveView):
    pass


class PrivateMixin(LoginRequiredMixin, UserIsOwnerMixin):
    pass


class ProtectedMixin(LoginRequiredMixin, UserIsMemberMixin):
    pass


class PublicMixin(LoginRequiredMixin):
    pass


class YeastMixin:
    owned = None
    active = None

    def is_owned(self):
        if self.owned is None:
            self.owned = self.kwargs['user'] == self.request.user.get_username()
        return self.owned

    def is_active(self):
        if self.active is None:
            self.active = not self.request.resolver_match.view_name.endswith('_draft')
        return self.active

    def get_all_read_kwargs(self, active):
        return self.Yeast.get_all_read_kwargs(self.kwargs, active)

    def get_object(self):
        active = self.is_active()
        kwargs = self.get_all_read_kwargs(active)
        return get_object_or_404(self.Yeast.Model, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.get_object()
        context['owned'] = self.is_owned()
        context['object'] = object
        if object.active:
            context['move_url'] = reverse(self.Yeast.name + '_move', kwargs=self.kwargs)
        else:
            context['move_url'] = reverse(self.Yeast.name + '_move_draft', kwargs=self.kwargs)
            context['publish_url'] = reverse(self.Yeast.name + '_publish_draft', kwargs=self.kwargs)
        context.update(self.Yeast.get_context_data(object))
        return context


class WriteYeastMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_active():
            name = self.Yeast.name
        else:
            name = self.Yeast.name + '_draft'
        context['url'] = reverse(name, kwargs=self.kwargs)
        return context


class YeastMoveView(WriteYeastMixin, FormView):
    form_class = YeastForm
    template_name = 'malt/yeast/move.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['Yeast'] = self.Yeast
        kwargs['user'] = self.request.user
        kwargs['active'] = self.is_active()
        kwargs['initial'].update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        read_kwargs = self.get_all_read_kwargs(form.active)
        self.Yeast.Model.objects.filter(**read_kwargs).update(**form.kwargs)
        if form.active:
            name = self.Yeast.name
        else:
            name = self.Yeast.name + '_draft'
        return redirect(reverse(name, kwargs=form.meta))


class YeastRemoveView(WriteYeastMixin, TemplateView):
    template_name = 'malt/yeast/remove.html'

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        object.delete()
        return redirect(reverse('index'))


class YeastPublishView(WriteYeastMixin, TemplateView):
    template_name = 'malt/yeast/publish.html'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        object_draft = self.get_object()

        kwargs = self.get_all_read_kwargs(True)
        try:
            object = self.Yeast.Model.objects.get(**kwargs)
        except self.Yeast.Model.DoesNotExist:
            object = self.get_object()
            object.pk = None
            object.active = True
            object.save()

            kwargs = {self.Yeast.name: object}
            for filter in self.Yeast.get_child_filters(object_draft):
                filter.update(**kwargs)

            object_draft.delete()
        else:
            names = set(field.name for field in self.Yeast.Model._meta.fields)

            exclude = {'id', 'timestamp'}
            for constraint in self.Yeast.Model._meta.constraints:
                if isinstance(constraint, models.UniqueConstraint):
                    exclude.update(constraint.fields)

            for name in names - exclude:
                temp = getattr(object, name)
                setattr(object, name, getattr(object_draft, name))
                setattr(object_draft, name, temp)

            object_draft.save()
            object.save()

            children_draft = []
            for filter in self.Yeast.get_child_filters(object_draft):
                children_draft.extend(child for child in filter)
                filter.delete()

            children = []
            for filter in self.Yeast.get_child_filters(object):
                children.extend(child for child in filter)
                filter.delete()

            for child in children_draft:
                setattr(child, self.Yeast.name, object)
                child.save()

            for child in children:
                setattr(child, self.Yeast.name, object_draft)
                child.save()

        return redirect(reverse(self.Yeast.name, kwargs=self.kwargs))


class CalendarMixin(YeastMixin):
    Yeast = CalendarYeast


class CalendarView(PrivateMixin, CalendarMixin, TemplateView):
    template_name = 'malt/yeast/calendar.html'


class CalendarMoveView(PrivateMixin, CalendarMixin, YeastMoveView):
    pass


class CalendarRemoveView(PrivateMixin, CalendarMixin, YeastRemoveView):
    pass


class CalendarPublishView(PrivateMixin, CalendarMixin, YeastPublishView):
    pass


class IndexView(PublicMixin, TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
