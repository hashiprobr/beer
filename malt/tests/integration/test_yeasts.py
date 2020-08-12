from beer.tests import IntegrationTestCase

from malt.tests.integration import YeastTests

from ...yeasts import CourseYeast


class CourseYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = CourseYeast()

    def test(self):
        pass
