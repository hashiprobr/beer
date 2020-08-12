from beer.tests import IntegrationTestCase

from malt.tests.integration import YeastTests

from ...yeasts import SheetYeast


class SheetYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = SheetYeast()

    def test(self):
        pass
