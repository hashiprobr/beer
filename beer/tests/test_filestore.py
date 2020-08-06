from io import BytesIO

from .. import public_storage, private_storage
from . import IntegrationTestCase


class StorageTests:
    name = 'n'

    content = b'c'
    empty_content = b''

    def save(self, name, content):
        file = BytesIO(content)
        self.storage.save(name, file)

    def assertFileExistsAfterSave(self, name, content):
        self.save(name, content)
        self.assertTrue(self.storage.exists(name))

    def assertFileDoesNotExistAfterSaveAndDelete(self, name, content):
        self.save(name, content)
        self.storage.delete(name)
        self.assertFalse(self.storage.exists(name))

    def assertFileHasSameContentAfterSave(self, name, expected):
        self.save(name, expected)
        with self.storage.open(name, 'rb') as file:
            actual = file.read()
        self.assertEqual(expected, actual)

    def testFileExistsAfterSave(self):
        self.assertFileExistsAfterSave(self.name, self.content)

    def testFileWithEmptyContentExistsAfterSave(self):
        self.assertFileExistsAfterSave(self.name, self.empty_content)

    def testFileDoesNotExistAfterSaveAndDelete(self):
        self.assertFileDoesNotExistAfterSaveAndDelete(self.name, self.content)

    def testFileWithEmptyContentDoesNotExistAfterSaveAndDelete(self):
        self.assertFileDoesNotExistAfterSaveAndDelete(self.name, self.empty_content)

    def testFileHasSameContentAfterSave(self):
        self.assertFileHasSameContentAfterSave(self.name, self.content)

    def testFileWithEmptyContentHasSameContentAfterSave(self):
        self.assertFileHasSameContentAfterSave(self.name, self.empty_content)


class PublicStorageTests(StorageTests, IntegrationTestCase):
    storage = public_storage


class PrivateStorageTests(StorageTests, IntegrationTestCase):
    storage = private_storage
