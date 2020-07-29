from urllib.parse import quote, parse_qs

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.views import generic
from shortuuid import uuid

from beer import public_storage, private_storage


CSRF_KEY = 'csrfmiddlewaretoken'

AUTH_MIXINS = [LoginRequiredMixin]


class TemplateDebugMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['debug'] = settings.TEMPLATE_DEBUG
        return context


class View(*AUTH_MIXINS, generic.View):
    pass


class UploadView(View):
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


class UploadCodeView(View):
    def post(self, request, *args, **kwargs):
        if len(request.FILES) != 1:
            return HttpResponseBadRequest()

        try:
            file = request.FILES['file']
        except KeyError:
            return HttpResponseBadRequest()

        body = request.POST.dict()
        del body[CSRF_KEY]

        for key, value in body.items():
            print(key, value)
        print(file)

        return HttpResponse('code')


class UploadAssetView(View):
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


class UploadAssetConfirmView(View):
    def get(self, request, *args, **kwargs):
        body = parse_qs(request.META['QUERY_STRING'], encoding='utf-8')

        try:
            key = body['key']
        except KeyError:
            return HttpResponseBadRequest()

        try:
            paths = key[0].split('/')
            uid = paths[-1]
        except IndexError:
            return HttpResponseBadRequest()

        print(uid)

        return HttpResponse('asset')


class TemplateView(*AUTH_MIXINS, TemplateDebugMixin, generic.TemplateView):
    pass


class IndexView(TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
