from io import BytesIO

from .. import public_storage, private_storage
from . import IntegrationTestCase


class StorageTests:
    name = 'n'

    content = b'c'
    blank_content = b''

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

    def assertFileHasSameContentAfterSave(self, name, expected_content):
        self.save(name, expected_content)
        with self.storage.open(name, 'rb') as file:
            actual_content = file.read()
        self.assertEqual(expected_content, actual_content)

    def testFileExistsAfterSave(self):
        self.assertFileExistsAfterSave(self.name, self.content)

    def testFileWithBlankContentExistsAfterSave(self):
        self.assertFileExistsAfterSave(self.name, self.blank_content)

    def testFileDoesNotExistAfterSaveAndDelete(self):
        self.assertFileDoesNotExistAfterSaveAndDelete(self.name, self.content)

    def testFileWithBlankContentDoesNotExistAfterSaveAndDelete(self):
        self.assertFileDoesNotExistAfterSaveAndDelete(self.name, self.blank_content)

    def testFileHasSameContentAfterSave(self):
        self.assertFileHasSameContentAfterSave(self.name, self.content)

    def testFileWithBlankContentHasSameContentAfterSave(self):
        self.assertFileHasSameContentAfterSave(self.name, self.blank_content)


class PublicStorageTests(StorageTests, IntegrationTestCase):
    storage = public_storage


class PrivateStorageTests(StorageTests, IntegrationTestCase):
    storage = private_storage
