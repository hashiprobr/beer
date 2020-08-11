from io import BytesIO

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from beer import public_storage
from beer.tests import IntegrationTestCase

from ...models import PowerUser, FolderAsset, FileAsset

User = get_user_model()


class PowerUserTests(IntegrationTestCase):
    def createValues(self):
        return User.objects.create_user('u')

    def create(self, user):
        PowerUser.objects.create(user=user)

    def retrieve(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def delete(self, user):
        PowerUser.objects.filter(user=user).delete()

    def assertDoesNotCreate(self, user):
        with self.assertRaises(IntegrityError):
            self.create(user)

    def assertRetrieves(self, user):
        self.assertTrue(self.retrieve(user))

    def assertDoesNotRetrieve(self, user):
        self.assertFalse(self.retrieve(user))

    def testDoesNotCreateWithNoneUser(self):
        _ = self.createValues()
        self.assertDoesNotCreate(None)

    def testDoesNotCreateWithSameUser(self):
        user = self.createValues()
        self.create(user)
        self.assertDoesNotCreate(user)

    def testRetrievesAfterCreate(self):
        user = self.createValues()
        self.create(user)
        self.assertRetrieves(user)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user = self.createValues()
        self.create(user)
        self.delete(user)
        self.assertDoesNotRetrieve(user)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user = self.createValues()
        self.create(user)
        user.delete()
        self.assertDoesNotRetrieve(user)


class FolderAssetTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        parent = FolderAsset.objects.create(user=user, parent=None, name='p')
        name = 'f'
        return user, parent, name

    def create(self, user, parent, name):
        FolderAsset.objects.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FolderAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def delete(self, user, parent, name):
        FolderAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertRetrieves(self, user, parent, name):
        self.assertTrue(self.retrieve(user, parent, name))

    def assertDoesNotRetrieve(self, user, parent, name):
        self.assertFalse(self.retrieve(user, parent, name))

    def testDoesNotCreateWithNoneUser(self):
        _, parent, name = self.createValues()
        self.assertDoesNotCreate(None, parent, name)

    def testDoesNotCreateWithNoneName(self):
        user, parent, _ = self.createValues()
        self.assertDoesNotCreate(user, parent, None)

    def testDoesNotCreateWithSameKey(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertDoesNotCreate(user, parent, name)

    def testRetrievesAfterCreate(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertRetrieves(user, parent, name)

    def testRetrievesAfterCreateWithNoneParent(self):
        user, _, name = self.createValues()
        self.create(user, None, name)
        self.assertRetrieves(user, None, name)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.delete(user, parent, name)
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        user.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteParent(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        parent.delete()
        self.assertDoesNotRetrieve(user, parent, name)


class FileAssetTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        parent = FolderAsset.objects.create(user=user, parent=None, name='p')
        name = 'f'
        return user, parent, name

    def create(self, user, parent, name):
        return FileAsset.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FileAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def delete(self, user, parent, name):
        FileAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertRetrieves(self, user, parent, name):
        self.assertTrue(self.retrieve(user, parent, name))

    def assertDoesNotRetrieve(self, user, parent, name):
        self.assertFalse(self.retrieve(user, parent, name))

    def assertDataDoesNotExist(self, key):
        self.assertFalse(public_storage.exists(key))

    def testDoesNotCreateWithNoneUser(self):
        _, parent, name = self.createValues()
        self.assertDoesNotCreate(None, parent, name)

    def testDoesNotCreateWithNoneName(self):
        user, parent, _ = self.createValues()
        self.assertDoesNotCreate(user, parent, None)

    def testDoesNotCreateWithSameKey(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertDoesNotCreate(user, parent, name)

    def testRetrievesAfterCreate(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertRetrieves(user, parent, name)

    def testRetrievesAfterCreateWithNoneParent(self):
        user, _, name = self.createValues()
        self.create(user, None, name)
        self.assertRetrieves(user, None, name)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.delete(user, parent, name)
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        user.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteParent(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        parent.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDataDoesNotExistAfterDelete(self):
        user, parent, name = self.createValues()
        file = self.create(user, parent, name)
        key = file.key()
        public_storage.save(key, BytesIO(b'c'))
        file.delete()
        self.assertDataDoesNotExist(key)
