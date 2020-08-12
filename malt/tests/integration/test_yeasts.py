import os

from beer.tests import IntegrationTestCase


class YeastTests:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def open(self, name):
        path = os.path.join(self.dir, name)
        with open(path) as file:
            data = file.read()
        return data


class CourseYeastTests(YeastTests, IntegrationTestCase):
    pass
