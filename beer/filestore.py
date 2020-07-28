import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from storages.backends.s3boto3 import S3Boto3Storage

from .s3 import sign_post


class OverwriteStorage:
    def save(self, name, content, max_length=None):
        if self.exists(name):
            self.delete(name)
        return super().save(name, content, max_length)


class LocalStorage(OverwriteStorage, FileSystemStorage):
    def post(self, name, redirect):
        body = {
            'action': self.action(),
            'key': name,
            'success_action_redirect': redirect,
        }
        return body


class PublicLocalStorage(LocalStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_BUCKET, settings.PUBLIC_LOCATION)
    base_url = '/{}/{}/'.format(settings.MEDIA_BUCKET, settings.PUBLIC_LOCATION)

    def action(self):
        return reverse('upload_asset_public')


class PrivateLocalStorage(LocalStorage):
    location = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_BUCKET, settings.PRIVATE_LOCATION)
    base_url = '/{}/{}/'.format(settings.MEDIA_BUCKET, settings.PRIVATE_LOCATION)

    def action(self):
        return reverse('upload_asset_private')


class RemoteStorage(OverwriteStorage, S3Boto3Storage):
    override_url = settings.AWS_S3_OVERRIDE_URL

    def url(self, name, parameters=None, expire=None):
        url = super().url(name, parameters, expire)
        if self.override_url:
            url = url.replace(self.endpoint_url, self.override_url)
        return url

    def post(self, name, redirect):
        key = '{}/{}'.format(self.location, name)
        return sign_post(self.bucket_name, key, redirect)


class StaticRemoteStorage(RemoteStorage):
    bucket_name = settings.STATIC_BUCKET
    location = settings.VERSION
    querystring_auth = False


class PublicRemoteStorage(RemoteStorage):
    bucket_name = settings.MEDIA_BUCKET
    location = settings.PUBLIC_LOCATION
    querystring_auth = False


class PrivateRemoteStorage(RemoteStorage):
    bucket_name = settings.MEDIA_BUCKET
    location = settings.PRIVATE_LOCATION
    querystring_auth = True
