from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.utils.module_loading import import_string

from .filestore import PublicLocalStorage, PrivateLocalStorage


def collapse(value):
    return ' '.join(value.strip().split())


def build_urlpatterns():
    urlpatterns = []

    for root in settings.STATICFILES_DIRS:
        if isinstance(root, (list, tuple)):
            prefix, root = root
        else:
            prefix = ''

        urlpatterns += static('{}{}/'.format(settings.STATIC_URL, prefix), document_root=root)

    urlpatterns += static(PublicLocalStorage.base_url, document_root=PublicLocalStorage.location)

    urlpatterns += static(PrivateLocalStorage.base_url, document_root=PrivateLocalStorage.location)

    return urlpatterns


def build_routepatterns(routeprefixes):
    routepatterns = []

    for prefix, path in routeprefixes.items():
        routesuffixes = import_string(path + '.routesuffixes')

        for suffix, consumer in routesuffixes.items():
            routepatterns.append(re_path(prefix + suffix, consumer))

    return routepatterns
