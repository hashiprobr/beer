from urllib.parse import quote, parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.detail import SingleObjectTemplateResponseMixin, BaseDetailView
from shortuuid import uuid

from beer import public_storage, private_storage

from .models import PowerUser, FolderAsset, FileAsset
from .forms import UserForm, AssetForm
from .caches import power_cache, member_cache
from .brewing import BrewError
from .brewery import Brewery

User = get_user_model()


PAGE_SIZE = 50

CSRF_KEY = 'csrfmiddlewaretoken'


class UserIsSuperMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserIsPowerMixin(UserPassesTestMixin):
    def test_func(self):
        return power_cache.get(self.request.user)


class AssetMixin:
    Asset = FolderAsset

    def get_objects(self, body):
        path = body['path']
        if path is None:
            names = []
            asset = None
        else:
            names = path.split('/')
            user = self.request.user
            parent = None
            for name in names[:-1]:
                try:
                    parent = FolderAsset.objects.get(user=user, parent=parent, name=name)
                except FolderAsset.DoesNotExist:
                    raise Http404()
            try:
                asset = self.Asset.objects.get(user=user, parent=parent, name=names[-1])
            except self.Asset.DoesNotExist:
                raise Http404()
        return names, asset


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


class UserMixin:
    def get_suffix(self):
        if self.request.GET:
            return '?' + self.request.GET.urlencode()
        else:
            return ''

    def get_success_url(self):
        return reverse('user_manage') + self.get_suffix()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suffix'] = self.get_suffix()
        return context


class UserManageView(LoginRequiredMixin, UserIsSuperMixin, UserMixin, FormView):
    form_class = UserForm
    template_name = 'malt/user/manage.html'

    def form_valid(self, form):
        for username, kwargs in form.users.items():
            user, created = User.objects.update_or_create(username=username, defaults=kwargs)
            if not created:
                power_cache.set(user, form.promote)
            if form.promote:
                PowerUser.objects.get_or_create(user=user)
            else:
                PowerUser.objects.filter(user=user).delete()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.all().order_by('username')
        paginator = Paginator(users, PAGE_SIZE)
        try:
            number = int(self.request.GET.get('page'))
            users = paginator.page(number)
        except (TypeError, EmptyPage):
            users = paginator.page(1)
        users.power_pks = PowerUser.objects.filter(user__in=users).values_list('user', flat=True)
        context['users'] = users
        context['focus'] = True
        return context


class UserAddView(LoginRequiredMixin, UserIsSuperMixin, UserMixin, MaltMixin, generic.edit.CreateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'malt/user/add.html'


class UserEditView(LoginRequiredMixin, UserIsSuperMixin, UserMixin, MaltMixin, generic.edit.UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'malt/user/edit.html'


class UserRemoveView(LoginRequiredMixin, UserIsSuperMixin, UserMixin, MaltMixin, generic.edit.DeleteView):
    model = User
    template_name = 'malt/user/remove.html'


class UserChangeView(LoginRequiredMixin, UserIsSuperMixin, UserMixin, MaltMixin, SingleObjectTemplateResponseMixin, BaseDetailView):
    model = User

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        power_cache.set(user, self.value)
        self.change(user)
        return HttpResponseRedirect(self.get_success_url())


class UserPromoteView(UserChangeView):
    value = True
    template_name = 'malt/user/promote.html'

    def change(self, user):
        PowerUser.objects.get_or_create(user=user)


class UserDemoteView(UserChangeView):
    value = False
    template_name = 'malt/user/demote.html'

    def change(self, user):
        PowerUser.objects.filter(user=user).delete()


class UploadView(LoginRequiredMixin, UserIsPowerMixin, generic.View):
    pass


class UploadPrepareView(UploadView):
    def post(self, request, *args, **kwargs):
        body = request.POST.dict()

        try:
            method = body.pop('method')
            name = body.pop('name')
        except KeyError:
            return HttpResponseBadRequest()

        if method == 'code':
            body['action'] = reverse('upload_code'),
            return JsonResponse(body)

        if method == 'asset':
            try:
                folder_pk = body['folder_pk']
            except KeyError:
                return HttpResponseBadRequest()

            uid = uuid()
            print(name, folder_pk, uid)

            name = '{}/assets/{}'.format(request.user.get_username(), uid)
            redirect = '{}://{}{}'.format(request.scheme, request.get_host(), reverse('upload_asset_confirm'))
            body = public_storage.post(name, redirect)

            if body['action'].startswith('/'):
                body[CSRF_KEY] = request.POST[CSRF_KEY]
            return JsonResponse(body)

        return HttpResponseNotFound()


class UploadCodeView(LoginRequiredMixin, UserIsPowerMixin, MaltMixin, ContextMixin, TemplateResponseMixin, generic.View):
    template_name = 'malt/error.html'

    def post(self, request, *args, **kwargs):
        meta = request.POST.dict()

        del meta[CSRF_KEY]

        brewery = Brewery()

        try:
            url = brewery.brew(request.FILES, meta)
        except BrewError as error:
            context = self.get_context_data(**kwargs)
            context['error'] = error
            return self.render_to_response(context)

        return HttpResponseRedirect(url)


class UploadAssetView(UploadView):
    def post(self, request, *args, **kwargs):
        if settings.CONTAINED:
            return HttpResponseNotFound()

        try:
            key = request.POST['key']
            redirect = request.POST['success_action_redirect']
        except KeyError:
            return HttpResponseBadRequest()

        if len(request.FILES) != 1:
            return HttpResponseBadRequest()

        try:
            file = request.FILES['file']
        except KeyError:
            return HttpResponseBadRequest()

        self.storage.save(key, file)

        return HttpResponseRedirect('{}?key={}'.format(redirect, quote(key, encoding='utf-8')))


class UploadAssetPublicView(UploadAssetView):
    storage = public_storage


class UploadAssetPrivateView(UploadAssetView):
    storage = private_storage


class UploadAssetConfirmView(UploadView):
    def get(self, request, *args, **kwargs):
        body = parse_qs(request.META['QUERY_STRING'], encoding='utf-8')

        try:
            key = body['key']
        except KeyError:
            return HttpResponseBadRequest()

        paths = key[0].split('/')

        try:
            uid = paths[-1]
        except IndexError:
            return HttpResponseBadRequest()

        print(uid)

        return HttpResponse('asset')


class AssetViewMixin(AssetMixin):
    objects = None

    def get_objects(self):
        if self.objects is None:
            self.objects = super().get_objects(self.kwargs)
        return self.objects

    def get_path(self, names):
        if names:
            return '/'.join(names)
        else:
            return None

    def get_url(self, names):
        path = self.get_path(names)
        if path is None:
            return reverse('asset_manage')
        else:
            return reverse('asset_folder', kwargs={'path': path})


class AssetFormView(FormView):
    form_class = AssetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        names, asset = self.get_objects()
        kwargs['Asset'] = self.Asset
        kwargs['user'] = self.request.user
        self.update(kwargs, names, asset)
        return kwargs

    def form_valid(self, form):
        names, asset = self.get_objects()
        name = form.cleaned_data['name']
        names = self.process(names, asset, name)
        return HttpResponseRedirect(self.get_url(names))


class AssetManageView(LoginRequiredMixin, UserIsPowerMixin, AssetViewMixin, AssetFormView):
    template_name = 'malt/asset/manage.html'

    def update(self, kwargs, names, asset):
        kwargs['parent'] = asset
        kwargs['child'] = None

    def process(self, names, asset, name):
        FolderAsset.objects.create(user=self.request.user, parent=asset, name=name)
        return names

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        names, asset = self.get_objects()
        context['prefix'] = self.get_path(names)
        if names:
            context['name'] = names.pop()
            context['parent_url'] = self.get_url(names)
        else:
            context['name'] = 'assets'
            context['parent_url'] = None
        context['folders'] = FolderAsset.objects.filter(user=self.request.user, parent=asset)
        context['files'] = FileAsset.objects.filter(user=self.request.user, parent=asset)
        context['focus'] = True
        return context


class SingleAssetViewMixin(AssetViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        names, asset = self.get_objects()
        context['name'] = names.pop()
        context['parent_url'] = self.get_url(names)
        if names:
            context['parent_name'] = names.pop()
            context['grandparent_url'] = self.get_url(names)
        else:
            context['parent_name'] = 'assets'
            context['grandparent_url'] = None
        return context


class AssetEditView(LoginRequiredMixin, UserIsPowerMixin, SingleAssetViewMixin, AssetFormView):
    template_name = 'malt/asset/edit.html'

    def update(self, kwargs, names, asset):
        kwargs['initial']['name'] = names[-1]
        kwargs['parent'] = asset.parent
        kwargs['child'] = asset

    def process(self, names, asset, name):
        asset.name = name
        asset.save()
        return names[:-1]


class AssetEditFileView(AssetEditView):
    Asset = FileAsset


class AssetRemoveView(LoginRequiredMixin, UserIsPowerMixin, SingleAssetViewMixin, TemplateView):
    template_name = 'malt/asset/remove.html'

    def post(self, request, *args, **kwargs):
        names, asset = self.get_objects()
        asset.delete()
        return HttpResponseRedirect(self.get_url(names[:-1]))


class AssetRemoveFileView(AssetRemoveView):
    Asset = FileAsset


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
