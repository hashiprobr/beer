from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError
from django.dispatch import receiver
from shortuuid import uuid

from beer import public_storage

User = get_user_model()


class PowerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Asset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=22)

    class Meta:
        abstract = True
        unique_together = [
            ('user', 'parent', 'name'),
        ]


class FolderAsset(Asset):
    label = 'folder'
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)


class FileAsset(Asset):
    label = 'file'
    parent = models.ForeignKey(FolderAsset, on_delete=models.CASCADE, null=True)
    uid = models.CharField(max_length=22)
    active = models.BooleanField(default=False)

    @classmethod
    def pop(cls, kwargs):
        if 'uid' in kwargs:
            raise IntegrityError('uid not allowed in kwargs')
        user = kwargs.pop('user', None)
        while True:
            uid = uuid()
            if not cls.objects.filter(user=user, uid=uid).exists():
                return user, uid

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        user, uid = cls.pop(kwargs)
        return cls.objects.create(user=user, uid=uid, **kwargs)

    @classmethod
    @transaction.atomic
    def get_or_create(cls, **kwargs):
        if 'defaults' in kwargs and 'uid' in kwargs['defaults']:
            raise IntegrityError('uid not allowed in defaults')
        user, uid = cls.pop(kwargs)
        return cls.objects.get_or_create(user=user, uid=uid, **kwargs)

    def key(self):
        return '{}/assets/{}'.format(self.user.get_username(), self.uid)


@receiver(models.signals.post_delete, sender=FileAsset)
def post_file_asset_delete(sender, instance, using, **kwargs):
    key = instance.key()
    if public_storage.exists(key):
        public_storage.delete(key)
