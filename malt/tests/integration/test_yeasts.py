from beer.tests import IntegrationTestCase

from ...yeasts import CalendarYeast, CourseYeast
from .test_brewing import YeastTests


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
