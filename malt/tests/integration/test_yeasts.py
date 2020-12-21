from beer.tests import IntegrationTestCase

from malt.tests.integration.test_brewing import YeastTests

from ...yeasts import CalendarYeast, CourseYeast


class CalendarYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = CalendarYeast()

    def test(self):
        pass


class CourseYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = CourseYeast()

    def test(self):
        pass
