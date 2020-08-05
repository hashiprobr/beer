from urllib.parse import quote, parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views import generic
from shortuuid import uuid

from beer import public_storage, private_storage

from .models import PowerUser
from .forms import UserManageForm
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


class UserIsMemberMixin(UserPassesTestMixin):
    def test_func(self):
        return True


class TemplateDebugMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['debug'] = settings.TEMPLATE_DEBUG
        return context


class TemplateView(TemplateDebugMixin, generic.TemplateView):
    pass


class FormView(TemplateDebugMixin, generic.FormView):
    pass


class UpdateView(TemplateDebugMixin, generic.edit.UpdateView):
    pass


class DeleteView(TemplateDebugMixin, generic.edit.DeleteView):
    pass


class PowerView(LoginRequiredMixin, UserIsPowerMixin, generic.View):
    pass


class MaltView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['power'] = power_cache.get(self.request.user)
        return context


class PublicMaltView(LoginRequiredMixin, MaltView):
    pass


class PrivateMaltView(LoginRequiredMixin, UserIsMemberMixin, MaltView):
    pass


class UserManageView(LoginRequiredMixin, UserIsSuperMixin, FormView):
    form_class = UserManageForm
    template_name = 'malt/user_manage.html'
    success_url = reverse_lazy('user_manage')

    def form_valid(self, form):
        for username, kwargs in form.users.items():
            user, _ = User.objects.update_or_create(username=username, defaults=kwargs)
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
        return context


class UserEditView(LoginRequiredMixin, UserIsSuperMixin, UpdateView):
    model = User
    fields = ['email', 'first_name', 'last_name']
    template_name = 'malt/user_edit.html'
    success_url = reverse_lazy('user_manage')


class UserRemoveView(LoginRequiredMixin, UserIsSuperMixin, DeleteView):
    model = User
    template_name = 'malt/user_delete.html'
    success_url = reverse_lazy('user_manage')


class UserChangeView(LoginRequiredMixin, UserIsSuperMixin, TemplateView):
    def get_user(self, kwargs):
        try:
            return User.objects.get(pk=kwargs['pk'])
        except User.DoesNotExist:
            raise Http404

    def post(self, request, *args, **kwargs):
        user = self.get_user(kwargs)
        power_cache.set(user, self.value)
        self.change(user)
        return HttpResponseRedirect(reverse('user_manage'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_user(kwargs)
        return context


class UserPromoteView(UserChangeView):
    value = True
    template_name = 'malt/user_promote.html'

    def change(self, user):
        power_user = PowerUser(user=user)
        power_user.save()


class UserDemoteView(UserChangeView):
    value = False
    template_name = 'malt/user_demote.html'

    def change(self, user):
        PowerUser.objects.filter(user=user).delete()


class UploadView(PowerView):
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


class UploadCodeView(PowerView):
    def post(self, request, *args, **kwargs):
        meta = request.POST.dict()

        del meta[CSRF_KEY]

        brewery = Brewery()

        try:
            url = brewery.brew(request.FILES, meta)
        except BrewError as error:
            context = {
                'power': power_cache.get(self.request.user),
                'error': error,
            }
            return TemplateResponse(request, 'malt/error.html', context)

        return HttpResponseRedirect(url)


class UploadAssetView(PowerView):
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


class UploadAssetConfirmView(PowerView):
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


class IndexView(PublicMaltView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
