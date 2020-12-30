from beer.tests import IntegrationTestCase

from malt.tests.integration.test_brewing import YeastTests

from ...yeasts import NodeYeast


class NodeYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = NodeYeast(None, [])

    def test(self):
        pass
