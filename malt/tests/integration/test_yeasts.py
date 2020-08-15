from beer.tests import IntegrationTestCase

from malt.tests.integration import YeastTests

from ...yeasts import CalendarYeast, CourseYeast


class CalendarYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = CalendarYeast(None, [])

    def test(self):
        pass


class CourseYeastTests(YeastTests, IntegrationTestCase):
    def setUp(self):
        self.yeast = CourseYeast(None, [])

    def test(self):
        pass
