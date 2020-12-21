import os

from ...brewing import BrewError


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

    def assertFerments(self, meta, name, sugars):
        try:
            self.yeast.ferment(meta, self.open(name), sugars)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotFerment(self, meta, name, sugars):
        with self.assertRaises(BrewError):
            self.yeast.ferment(meta, self.open(name), sugars)

    def assertReferments(self, meta, sugars):
        try:
            self.yeast.referment(meta, sugars)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotReferment(self, meta, sugars):
        with self.assertRaises(BrewError):
            self.yeast.referment(meta, sugars)
