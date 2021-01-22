from django.db.models.signals import post_init, post_save, post_delete
from django.dispatch import receiver

from beer import public_storage

from .models import FileAsset


@receiver(post_init, sender=FileAsset)
def post_init_file_asset(**kwargs):
    file_asset = kwargs['instance']
    try:
        user = file_asset.user
        name = file_asset.name
        uid = file_asset.uid
    except AttributeError:
        return
    if user is not None and name is not None and uid is not None:
        file_asset.old_key = file_asset.key()


@receiver(post_save, sender=FileAsset)
def post_save_file_asset(**kwargs):
    file_asset = kwargs['instance']
    try:
        old_key =  file_asset.old_key
    except AttributeError:
        return
    key = file_asset.key()
    if key != old_key and public_storage.exists(old_key):
        public_storage.move(old_key, key)


@receiver(post_delete, sender=FileAsset)
def post_delete_file_asset(**kwargs):
    file_asset = kwargs['instance']
    key = file_asset.key()
    public_storage.delete(key)
