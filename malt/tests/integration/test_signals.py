from io import BytesIO

from django.contrib.auth import get_user_model

from beer import public_storage
from beer.tests import IntegrationTestCase

from ...models import FolderAsset, FileAsset

User = get_user_model()


class FileAssetPostDeleteTests(IntegrationTestCase):
    def setUp(self):
        user = User.objects.create_user('u')
        grand_parent = FolderAsset.objects.create(user=user, parent=None, name='gp')
        parent = FolderAsset.objects.create(user=user, parent=grand_parent, name='p')
        self.file_asset = FileAsset.objects.create(user=user, parent=parent, name='f')
        self.key = self.file_asset.key()
        public_storage.save(self.key, BytesIO(b'c'))

    def assertExists(self):
        self.assertTrue(public_storage.exists(self.key))

    def assertDoesNotExist(self):
        self.assertFalse(public_storage.exists(self.key))

    def assertDeletes(self):
        self.file_asset.delete()
        self.assertDoesNotExist()

    def testExists(self):
        self.assertExists()

    def testDeletes(self):
        self.assertDeletes()
