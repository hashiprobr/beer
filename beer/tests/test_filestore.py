from io import BytesIO

from .. import public_storage, private_storage
from ..filestore import StorageError
from . import IntegrationTestCase


class StorageTests:
    name = 'n'
    empty_name = ''

    content = b'c'
    other_content = b'oc'
    empty_content = b''

    def save(self, name, content):
        file = BytesIO(content)
        return self.storage.save(name, file)

    def retrieve(self, name):
        with self.storage.open(name, 'rb') as file:
            content = file.read()
        return content

    def delete(self, name):
        self.storage.delete(name)

    def assertExists(self, name, content):
        self.assertTrue(self.storage.exists(name))
        self.assertEqual(content, self.retrieve(name))

    def assertDoesNotExist(self, name):
        self.assertFalse(self.storage.exists(name))
        with self.assertRaises(FileNotFoundError):
            self.retrieve(name)

    def assertCreates(self, name, content):
        self.assertEqual(name, self.save(name, content))
        self.assertExists(name, content)

    def assertDoesNotCreate(self, name, content):
        with self.assertRaises(StorageError):
            self.save(name, content)

    def assertDeletes(self, name):
        self.delete(name)
        self.assertDoesNotExist(name)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.name)

    def testCreates(self):
        self.assertCreates(self.name, self.content)

    def testDoesNotCreateWithEmptyName(self):
        self.assertDoesNotCreate(self.empty_name, self.content)

    def testCreatesWithEmptyContent(self):
        self.assertCreates(self.name, self.empty_content)

    def testUpdates(self):
        self.save(self.name, self.content)
        self.assertCreates(self.name, self.other_content)

    def testUpdatesWithEmptyContent(self):
        self.save(self.name, self.content)
        self.assertCreates(self.name, self.empty_content)

    def testDeletes(self):
        self.save(self.name, self.content)
        self.assertDeletes(self.name)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.name)

    def testDeletesWithEmptyContent(self):
        self.save(self.name, self.empty_content)
        self.assertDeletes(self.name)


class NonEmptyStorageTests(StorageTests):
    size = 3

    def setUp(self):
        for i in range(self.size):
            self.save(str(i), bytes(i))

    def tearDown(self):
        for i in range(self.size):
            self.assertExists(str(i), bytes(i))


class PublicStorageTests(StorageTests, IntegrationTestCase):
    storage = public_storage


class PublicNonEmptyStorageTests(NonEmptyStorageTests, IntegrationTestCase):
    storage = public_storage


class PrivateStorageTests(StorageTests, IntegrationTestCase):
    storage = private_storage


class PrivateNonEmptyStorageTests(NonEmptyStorageTests, IntegrationTestCase):
    storage = private_storage
