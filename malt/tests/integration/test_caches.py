from django.contrib.auth import get_user_model

from beer.tests import IntegrationTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class PowerCacheTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def setUp(self):
        self.user = self.create(self.username)

    def create(self, username):
        return User.objects.create_user(username)

    def promote(self):
        PowerUser.objects.create(user=self.user)

    def assertPower(self):
        self.assertTrue(power_cache.get(self.user))

    def assertNotPower(self):
        self.assertFalse(power_cache.get(self.user))

    def testNotPowerBeforePromote(self):
        self.assertNotPower()

    def testPowerBeforePromoteIfCached(self):
        power_cache.set(self.user, True)
        self.assertPower()

    def testNotPowerBeforePromoteIfOtherCached(self):
        other_user = self.create(self.other_username)
        power_cache.set(other_user, True)
        self.assertNotPower()

    def testPowerAfterPromote(self):
        self.promote()
        self.assertPower()

    def testNotPowerAfterPromoteIfCached(self):
        power_cache.set(self.user, False)
        self.promote()
        self.assertNotPower()

    def testPowerAfterPromoteIfOtherCached(self):
        other_user = self.create(self.other_username)
        power_cache.set(other_user, False)
        self.promote()
        self.assertPower()
