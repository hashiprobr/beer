from django.db.models.signals import post_delete
from django.dispatch import receiver

from beer import public_storage

from .models import FileAsset


@receiver(post_delete, sender=FileAsset)
def post_delete_file_asset(sender, instance, using, **kwargs):
    key = instance.key()
    public_storage.delete(key)
