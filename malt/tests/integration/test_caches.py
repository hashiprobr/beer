from django.contrib.auth import get_user_model

from beer.tests import IntegrationTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class PowerCacheTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def assertPower(self, user):
        self.assertTrue(power_cache.get(user))

    def assertNotPower(self, user):
        self.assertFalse(power_cache.get(user))

    def testNotPowerBeforeCreate(self):
        user = User.objects.create_user(self.username)
        self.assertNotPower(user)

    def testPowerBeforeCreateIfCached(self):
        user = User.objects.create_user(self.username)
        power_cache.set(user, True)
        self.assertPower(user)

    def testNotPowerBeforeCreateIfOtherCached(self):
        user = User.objects.create_user(self.username)
        other_user = User.objects.create_user(self.other_username)
        power_cache.set(other_user, True)
        self.assertNotPower(user)

    def testPowerAfterCreate(self):
        user = User.objects.create_user(self.username)
        PowerUser.objects.create(user=user)
        self.assertPower(user)

    def testNotPowerAfterCreateIfCached(self):
        user = User.objects.create_user(self.username)
        PowerUser.objects.create(user=user)
        power_cache.set(user, False)
        self.assertNotPower(user)

    def testPowerAfterCreateIfOtherCached(self):
        user = User.objects.create_user(self.username)
        other_user = User.objects.create_user(self.other_username)
        PowerUser.objects.create(user=user)
        power_cache.set(other_user, False)
        self.assertPower(user)
