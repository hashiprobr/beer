from django.contrib.auth import get_user_model

from beer.tests import IntegrationTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class PowerCacheTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def assertIsPower(self, user):
        self.assertTrue(power_cache.get(user))

    def assertIsNotPower(self, user):
        self.assertFalse(power_cache.get(user))

    def testIsNotPowerBeforeCreate(self):
        user = User.objects.create_user(self.username)
        self.assertIsNotPower(user)

    def testIsPowerBeforeCreateIfCached(self):
        user = User.objects.create_user(self.username)
        power_cache.set(user, True)
        self.assertIsPower(user)

    def testIsNotPowerBeforeCreateIfOtherCached(self):
        user = User.objects.create_user(self.username)
        other_user = User.objects.create_user(self.other_username)
        power_cache.set(other_user, True)
        self.assertIsNotPower(user)

    def testIsPowerAfterCreate(self):
        user = User.objects.create_user(self.username)
        power_user = PowerUser(user=user)
        power_user.save()
        self.assertIsPower(user)

    def testIsNotPowerAfterCreateIfCached(self):
        user = User.objects.create_user(self.username)
        power_user = PowerUser(user=user)
        power_user.save()
        power_cache.set(user, False)
        self.assertIsNotPower(user)

    def testIsPowerAfterCreateIfOtherCached(self):
        user = User.objects.create_user(self.username)
        other_user = User.objects.create_user(self.other_username)
        power_user = PowerUser(user=user)
        power_user.save()
        power_cache.set(other_user, False)
        self.assertIsPower(user)
