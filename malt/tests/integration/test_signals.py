from io import BytesIO

from django.contrib.auth import get_user_model

from beer import public_storage
from beer.tests import IntegrationTestCase

from ...models import FolderAsset, FileAsset

User = get_user_model()


class FileAssetSignalTests(IntegrationTestCase):
    def setUp(self):
        user = User.objects.create_user('u')
        grand_parent = FolderAsset.objects.create(user=user, parent=None, name='gpn')
        parent = FolderAsset.objects.create(user=user, parent=grand_parent, name='pn')
        self.file_asset = FileAsset.objects.create(user=user, parent=parent, name='n')
        key = self.file_asset.key()
        file = BytesIO(b'c')
        public_storage.save(key, file)

    def exists(self, key):
        return public_storage.exists(key)

    def assertExists(self, key):
        self.assertTrue(self.exists(key))

    def assertDoesNotExist(self, key):
        self.assertFalse(self.exists(key))

    def testExists(self):
        key = self.file_asset.key()
        self.assertExists(key)

    def testDeletes(self):
        key = self.file_asset.key()
        self.file_asset.delete()
        self.assertDoesNotExist(key)

    def testExtends(self):
        key = self.file_asset.key()
        self.file_asset.name = 'n.e'
        self.file_asset.save()
        self.assertDoesNotExist(key)
        key = self.file_asset.key()
        self.assertExists(key)
