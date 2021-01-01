from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.detail import SingleObjectTemplateResponseMixin, BaseDetailView

from beer import public_storage

from .models import PowerUser, FolderAsset, FileAsset
from .forms import UserForm, AssetForm
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


class UserIsMemberMixin(UserPassesTestMixin):
    def test_func(self):
        return True


class AssetMixin:
    Asset = FolderAsset

    def get_objects(self, path):
        if path:
            names = path.split('/')
            parent = None
            for name in names[:-1]:
                parent = get_object_or_404(FolderAsset, user=self.request.user, parent=parent, name=name)
            asset = get_object_or_404(self.Asset, user=self.request.user, parent=parent, name=names[-1])
        else:
            names = []
            asset = None
        return names, asset


class AssetPathMixin:
    def get_url(self, names):
        if names:
            return reverse('asset_folder', kwargs={'path': '/'.join(names)})
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


class UserViewMixin:
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


class UserManageView(LoginRequiredMixin, UserIsSuperMixin, UserViewMixin, FormView):
    form_class = UserForm
    template_name = 'malt/user/manage.html'

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
            filter = self.request.GET['filter'].strip()
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


class UserAddView(LoginRequiredMixin, UserIsSuperMixin, FormUserViewMixin, generic.edit.CreateView):
    template_name = 'malt/user/add.html'


class UserEditView(LoginRequiredMixin, UserIsSuperMixin, FormUserViewMixin, generic.edit.UpdateView):
    template_name = 'malt/user/edit.html'


class UserRemoveView(LoginRequiredMixin, UserIsSuperMixin, SingleUserViewMixin, generic.edit.DeleteView):
    template_name = 'malt/user/remove.html'


class UserChangeView(LoginRequiredMixin, UserIsSuperMixin, SingleUserViewMixin, SingleObjectTemplateResponseMixin, BaseDetailView):
    def post(self, request, *args, **kwargs):
        user = self.get_object()
        power_cache.set(user, self.value)
        self.change(user)
        return redirect(self.get_success_url())


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


class UploadManageView(LoginRequiredMixin, UserIsPowerMixin, AssetMixin, generic.View):
    def post(self, request, *args, **kwargs):
        body = request.POST.dict()

        try:
            method = body.pop('method')
            name = body.pop('name')
        except KeyError:
            return HttpResponseBadRequest()

        if method == 'code':
            body['action'] = reverse('upload_code')
            return JsonResponse(body)

        if method == 'asset':
            if not name.strip():
                return HttpResponseBadRequest('The file name is required.')
            if '/' in name:
                return HttpResponseBadRequest('The file name cannot have slashes.')
            expected = FileAsset.name.field.max_length
            actual = len(name)
            if expected < actual:
                return HttpResponseBadRequest('Ensure the file name has at most {} characters (it has {}).'.format(expected, actual))

            try:
                path = body['path']
            except KeyError:
                return HttpResponseBadRequest()

            _, parent = self.get_objects(path)

            asset, _ = FileAsset.objects.get_or_create(user=request.user, parent=parent, name=name)
            key = asset.key()
            redirect_url = '{}://{}{}'.format(request.scheme, request.get_host(), reverse('upload_asset_confirm'))

            body = public_storage.post(key, redirect_url)

            try:
                body[CSRF_KEY] = request.POST[CSRF_KEY]
            except KeyError:
                pass
            return JsonResponse(body)

        return HttpResponseNotFound()


class UploadCodeView(LoginRequiredMixin, UserIsPowerMixin, MaltMixin, TemplateResponseMixin, ContextMixin, generic.View):
    template_name = 'malt/error.html'

    def post(self, request, *args, **kwargs):
        brewery = Brewery(request.user, [])

        meta = request.POST.dict()
        try:
            del meta[CSRF_KEY]
        except KeyError:
            pass

        try:
            url = brewery.brew(request.FILES, meta)
        except BrewError as error:
            context = self.get_context_data(**kwargs)
            context['error'] = error
            return self.render_to_response(context)

        return redirect(url)


class UploadAssetView(LoginRequiredMixin, UserIsPowerMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if settings.CONTAINED:
            return HttpResponseNotFound()

        try:
            key = request.POST['key']
            url = request.POST['success_action_redirect']
        except KeyError:
            return HttpResponseBadRequest()

        if not key.strip():
            return HttpResponseBadRequest()

        if not url.startswith('http://'):
            return HttpResponseBadRequest()

        if len(request.FILES) != 1:
            return HttpResponseBadRequest()

        try:
            file = request.FILES['file']
        except KeyError:
            return HttpResponseBadRequest()

        public_storage.save(key, file)

        return redirect('{}?{}'.format(url, urlencode({'key': key}, safe='/')))


class UploadAssetConfirmView(LoginRequiredMixin, UserIsPowerMixin, AssetPathMixin, generic.View):
    def get(self, request, *args, **kwargs):
        body = request.GET.dict()

        try:
            key = body['key']
        except KeyError:
            return HttpResponseBadRequest()

        paths = key.split('/')

        asset = get_object_or_404(FileAsset, user=request.user, uid=paths[-1])

        if not asset.active and public_storage.exists(asset.key()):
            asset.active = True
            asset.save()

        return redirect(self.get_url(asset.names()))


class AssetViewMixin(AssetMixin, AssetPathMixin):
    objects = None

    def get_objects(self):
        if self.objects is None:
            self.objects = super().get_objects(self.kwargs['path'])
        return self.objects


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
        return redirect(self.get_url(names))


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
        context['prefix'] = self.kwargs['path']
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


class SpecificAssetViewMixin(AssetViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        names, _ = self.get_objects()
        context['name'] = names.pop()
        context['parent_url'] = self.get_url(names)
        if names:
            context['parent_name'] = names.pop()
            context['grandparent_url'] = self.get_url(names)
        else:
            context['parent_name'] = 'assets'
            context['grandparent_url'] = None
        return context


class AssetEditView(LoginRequiredMixin, UserIsPowerMixin, SpecificAssetViewMixin, AssetFormView):
    template_name = 'malt/asset/edit.html'

    def update(self, kwargs, names, asset):
        kwargs['parent'] = asset.parent
        kwargs['child'] = asset
        kwargs['initial']['name'] = names[-1]

    def process(self, names, asset, name):
        asset.name = name
        asset.save()
        return names[:-1]


class AssetEditFileView(AssetEditView):
    Asset = FileAsset


class AssetRemoveView(LoginRequiredMixin, UserIsPowerMixin, SpecificAssetViewMixin, TemplateView):
    template_name = 'malt/asset/remove.html'

    def post(self, request, *args, **kwargs):
        names, asset = self.get_objects()
        asset.delete()
        return redirect(self.get_url(names[:-1]))


class AssetRemoveFileView(AssetRemoveView):
    Asset = FileAsset


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context


class YeastView(LoginRequiredMixin, TemplateView):
    def get_object(self):
        yeast = self.Yeast(None, [])
        active = not self.request.resolver_match.view_name.endswith('_draft')
        try:
            return yeast.get_object(active, self.kwargs)
        except yeast.Model.DoesNotExist:
            raise Http404()


class CalendarView(YeastView):
    Yeast = CalendarYeast
    template_name = 'malt/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.get_object()
        context['active'] = calendar.active
        return context
