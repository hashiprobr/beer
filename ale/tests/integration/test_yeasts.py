from beer.tests import IntegrationTestCase

from malt.tests.integration import YeastTests

from ...yeasts import NodeYeast


class NodeYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = NodeYeast()

    def test(self):
        pass
