from django.apps import AppConfig


class MaltConfig(AppConfig):
    name = 'malt'

    def ready(self):
        from . import signals
