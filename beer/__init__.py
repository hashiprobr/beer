from django.conf import settings
from django.utils.module_loading import import_string

PublicStorage = import_string(settings.PUBLICFILES_STORAGE)
PrivateStorage = import_string(settings.PRIVATEFILES_STORAGE)

public_storage = PublicStorage()
private_storage = PrivateStorage()
