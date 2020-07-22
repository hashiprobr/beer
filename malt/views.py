from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'malt/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['version'] = '{}.{}'.format(settings.VERSION, settings.PATCH_VERSION)
        return context
