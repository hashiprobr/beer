from django.contrib.auth import get_user_model

from beer.tests import IntegrationTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class PowerCacheTests(IntegrationTestCase):
    def setUp(self):
        self.user = User.objects.create_user('u')

    def promote(self):
        PowerUser.objects.create(user=self.user)

    def demote(self):
        PowerUser.objects.filter(user=self.user).delete()

    def get(self):
        return power_cache.get(self.user)

    def set(self, value):
        power_cache.set(self.user, value)

    def assertPower(self):
        self.assertTrue(self.get())

    def assertNotPower(self):
        self.assertFalse(self.get())

    def testNotPower(self):
        self.assertNotPower()

    def testNotPowerAfterGet(self):
        self.get()
        self.assertNotPower()

    def testNotPowerAfterSetFalse(self):
        self.set(False)
        self.assertNotPower()

    def testPowerAfterSetTrue(self):
        self.set(True)
        self.assertPower()

    def testPowerAfterPromote(self):
        self.promote()
        self.assertPower()

    def testNotPowerAfterGetPromote(self):
        self.get()
        self.promote()
        self.assertNotPower()

    def testPowerAfterPromoteGet(self):
        self.promote()
        self.get()
        self.assertPower()

    def testNotPowerAfterSetFalsePromote(self):
        self.set(False)
        self.promote()
        self.assertNotPower()

    def testNotPowerAfterPromoteSetFalse(self):
        self.promote()
        self.set(False)
        self.assertNotPower()

    def testPowerAfterSetTruePromote(self):
        self.set(True)
        self.promote()
        self.assertPower()

    def testPowerAfterPromoteSetTrue(self):
        self.promote()
        self.set(True)
        self.assertPower()

    def testNotPowerAfterPromoteDemote(self):
        self.promote()
        self.demote()
        self.assertNotPower()

    def testNotPowerAfterGetPromoteDemote(self):
        self.get()
        self.promote()
        self.demote()
        self.assertNotPower()

    def testPowerAfterPromoteGetDemote(self):
        self.promote()
        self.get()
        self.demote()
        self.assertPower()

    def testNotPowerAfterPromoteDemoteGet(self):
        self.promote()
        self.demote()
        self.get()
        self.assertNotPower()

    def testNotPowerAfterSetFalsePromoteDemote(self):
        self.set(False)
        self.promote()
        self.demote()
        self.assertNotPower()

    def testNotPowerAfterPromoteSetFalseDemote(self):
        self.promote()
        self.set(False)
        self.demote()
        self.assertNotPower()

    def testNotPowerAfterPromoteDemoteSetFalse(self):
        self.promote()
        self.demote()
        self.set(False)
        self.assertNotPower()

    def testPowerAfterSetTruePromoteDemote(self):
        self.set(True)
        self.promote()
        self.demote()
        self.assertPower()

    def testPowerAfterPromoteSetTrueDemote(self):
        self.promote()
        self.set(True)
        self.demote()
        self.assertPower()

    def testPowerAfterPromoteDemoteSetTrue(self):
        self.promote()
        self.demote()
        self.set(True)
        self.assertPower()
