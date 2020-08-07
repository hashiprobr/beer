from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError
from django.dispatch import receiver
from shortuuid import uuid

from beer import public_storage

User = get_user_model()


class PowerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class AssetFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=15)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ('user', 'parent', 'name'),
        ]


class AssetFile(models.Model):
    folder = models.ForeignKey(AssetFolder, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    uid = models.CharField(max_length=22)
    active = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('folder', 'name'),
        ]

    @classmethod
    def pop(cls, kwargs):
        if 'uid' in kwargs:
            raise IntegrityError('uid not allowed in kwargs')
        folder = kwargs.pop('folder', None)
        if not isinstance(folder, AssetFolder):
            raise IntegrityError('folder required in kwargs')
        while True:
            uid = uuid()
            if not cls.objects.filter(folder__user=folder.user, uid=uid).exists():
                return folder, uid

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        folder, uid = cls.pop(kwargs)
        return cls.objects.create(folder=folder, uid=uid, **kwargs)

    @classmethod
    @transaction.atomic
    def get_or_create(cls, **kwargs):
        if 'defaults' in kwargs and 'uid' in kwargs['defaults']:
            raise IntegrityError('uid not allowed in defaults')
        folder, uid = cls.pop(kwargs)
        return cls.objects.get_or_create(folder=folder, uid=uid, **kwargs)

    def key(self):
        return '{}/assets/{}'.format(self.folder.user.get_username(), self.uid)


@receiver(models.signals.post_delete, sender=AssetFile)
def post_asset_file_delete(sender, instance, using, **kwargs):
    key = instance.key()
    if public_storage.exists(key):
        public_storage.delete(key)
