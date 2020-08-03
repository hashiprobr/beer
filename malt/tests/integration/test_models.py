from django.contrib.auth import get_user_model
from django.db import IntegrityError

from beer.tests import IntegrationTestCase

from ...models import PowerUser

User = get_user_model()


class PowerUserTests(IntegrationTestCase):
    def createUser(self):
        return User.objects.create_user('u')

    def create(self, user):
        power_user = PowerUser(user=user)
        power_user.save()

    def retrieve(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def delete(self, user):
        PowerUser.objects.filter(user=user).delete()

    def assertRaisesValueErrorIfCreate(self, user):
        with self.assertRaises(ValueError):
            self.create(user)

    def assertRaisesIntegrityErrorIfCreate(self, user):
        with self.assertRaises(IntegrityError):
            self.create(user)

    def assertRetrieves(self, user):
        self.assertTrue(self.retrieve(user))

    def assertDoesNotRetrieve(self, user):
        self.assertFalse(self.retrieve(user))

    def testRaisesIntegrityErrorIfCreateWithNoneUser(self):
        self.assertRaisesIntegrityErrorIfCreate(None)

    def testRaisesValueErrorIfCreateWithNewUser(self):
        user = User()
        self.assertRaisesValueErrorIfCreate(user)

    def testRaisesIntegrityErrorIfCreateWithSameUser(self):
        user = self.createUser()
        self.create(user)
        self.assertRaisesIntegrityErrorIfCreate(user)

    def testRetrievesByUserAfterCreate(self):
        user = self.createUser()
        self.create(user)
        self.assertRetrieves(user)

    def testDoesNotRetrieveAfterCreateAndDeleteByUser(self):
        user = self.createUser()
        self.create(user)
        self.delete(user)
        self.assertDoesNotRetrieve(user)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user = self.createUser()
        self.create(user)
        user.delete()
        self.assertDoesNotRetrieve(user)
