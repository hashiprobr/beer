from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.views import generic

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
        try:
            method = request.POST['method']
        except KeyError:
            return HttpResponseBadRequest()
        if method == 'code':
            body = {
                'action': reverse('upload_code'),
                CSRF_KEY: request.POST[CSRF_KEY],
            }
            return JsonResponse(body)
        if method == 'asset':
            try:
                name = request.POST['name']
            except KeyError:
                return HttpResponseBadRequest()
            redirect = '{}://{}{}'.format(request.scheme, request.get_host(), reverse('upload_asset_complete'))
            body = public_storage.post('{}/{}'.format(request.user.get_username(), name), redirect)
            return JsonResponse(body)
        return HttpResponseNotFound()


class UploadCodeView(View):
    def post(self, request, *args, **kwargs):
        return HttpResponse('code')


class UploadAssetView(View):
    def post(self, request, *args, **kwargs):
        if settings.CONTAINED:
            try:
                redirect = request.POST['success_action_redirect']
            except KeyError:
                return HttpResponseBadRequest()
            return HttpResponseRedirect(redirect)
        return HttpResponseNotFound()


class UploadAssetPublicView(UploadAssetView):
    storage = public_storage


class UploadAssetPrivateView(UploadAssetView):
    storage = private_storage


class UploadAssetCompleteView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('asset')


class TemplateView(*AUTH_MIXINS, TemplateDebugMixin, generic.TemplateView):
    pass


class IndexView(TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
