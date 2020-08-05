import os

from io import BytesIO

from django.core.files import File
from django.utils.datastructures import MultiValueDict

from beer.tests import UnitTestCase

from ...brewing import BrewError, YeastError, Yeast
from ...enzymes import EnzymeError, Enzyme
from ...brewery import Brewery


class MockEnzyme(Enzyme):
    extension = 'mock'


class FailMockEnzyme(MockEnzyme):
    def convert(self, content):
        raise EnzymeError()


class PassMockEnzyme(MockEnzyme):
    def __init__(self, members):
        self.members = members

    def convert(self, content):
        return self.members


class FailMockYeast(Yeast):
    def clean(self, meta):
        raise YeastError()


class PassMockYeast(Yeast):
    def clean(self, meta):
        return meta

    def ferment(self, meta, data, sugars):
        return meta, data, sugars

    def referment(self, meta, sugars):
        return meta, sugars


class BreweryTests(UnitTestCase):
    MockYeasts = {
        'fail': FailMockYeast(),
        'pass': PassMockYeast(),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def setUp(self):
        self.brewery = Brewery()

    def open(self, name):
        path = os.path.join(self.dir, name)
        with open(path, 'rb') as file:
            content = file.read()
        return content

    def mock(self, names):
        return PassMockEnzyme([(0, name, self.open(name)) for name in names])

    def grow(self, name):
        return self.brewery.grow(self.open(name), self.MockYeasts)

    def prime(self, meta):
        self.brewery.prime(meta, [], self.MockYeasts)

    def brew(self, names, meta, enzymes):
        files = MultiValueDict()
        for key, name in names.items():
            files[key] = File(BytesIO(self.open(name)), name)
        return self.brewery.brew(files, meta, enzymes, self.MockYeasts)

    def assertGrows(self, name, expected):
        _, _, actual = self.grow(name)
        self.assertIsNotNone(input)
        self.assertEquals(expected, actual)

    def assertDoesNotGrow(self, name):
        self.assertIsNone(self.grow(name))

    def assertPrimes(self, meta):
        try:
            self.prime(meta)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotPrime(self, meta):
        with self.assertRaises(BrewError):
            self.prime(meta)

    def assertBrews(self, names, meta, enzymes, expected):
        try:
            actual = self.brew(names, meta, enzymes)
        except BrewError:
            self.fail('BrewError raised')
        self.assertEquals(expected, actual)

    def assertDoesNotBrew(self, names, meta, enzymes):
        with self.assertRaises(BrewError):
            self.brew(names, meta, enzymes)

    def testGrows(self):
        self.assertGrows('pass.txt', 'c\n')

    def testGrowsWithLowerSeparator(self):
        self.assertGrows('lower-separator.txt', 'c\n...\n')

    def testGrowsWithUpperSeparator(self):
        self.assertGrows('upper-separator.txt', '...\nc\n')

    def testGrowsWithThreeSeparators(self):
        self.assertGrows('three-separators.txt', '...\nc\n...\n')

    def testDoesNotGrowWithoutSeparator(self):
        self.assertDoesNotGrow('no-separator.txt')

    def testDoesNotGrowWithLineSeparator(self):
        self.assertDoesNotGrow('line-separator.txt')

    def testDoesNotGrowWithSpaceSeparator(self):
        self.assertDoesNotGrow('space-separator.txt')

    def testDoesNotGrowWithWrongSeparator(self):
        self.assertDoesNotGrow('wrong-separator.txt')

    def testDoesNotGrowIfBinary(self):
        self.assertDoesNotGrow('binary.txt')

    def testDoesNotGrowIfInvalid(self):
        self.assertDoesNotGrow('invalid.txt')

    def testDoesNotGrowIfList(self):
        self.assertDoesNotGrow('list.txt')

    def testDoesNotGrowWithoutType(self):
        self.assertDoesNotGrow('no-type.txt')

    def testDoesNotGrowWithWrongType(self):
        self.assertDoesNotGrow('wrong-type.txt')

    def testDoesNotGrowIfRaisesYeastError(self):
        self.assertDoesNotGrow('fail.txt')

    def testPrimes(self):
        self.assertPrimes({'view_name': 'pass'})

    def testDoesNotPrimeWithoutType(self):
        self.assertDoesNotPrime({'mock': 'pass'})

    def testDoesNotPrimeWithWrongType(self):
        self.assertDoesNotPrime({'view_name': 'mock'})

    def testDoesNotPrimeIfRaisesYeastError(self):
        self.assertDoesNotPrime({'view_name': 'fail'})

    def testBrews(self):
        names = {'file': 'pass.txt'}
        meta = {'date': 0}
        enzymes = []
        expected = {}, 'c\n', []
        self.assertBrews(names, meta, enzymes, expected)

    def testDoesNotBrewWithoutFile(self):
        names = {}
        meta = {'date': 0}
        enzymes = []
        self.assertDoesNotBrew(names, meta, enzymes)

    def testDoesNotBrewWithTwoFiles(self):
        names = {'file': 'pass.txt', 'mock': 'lower-separator.txt'}
        meta = {'date': 0}
        enzymes = []
        self.assertDoesNotBrew(names, meta, enzymes)

    def testDoesNotBrewIfInputNotFile(self):
        names = {'mock': 'pass.txt'}
        meta = {'date': 0}
        enzymes = []
        self.assertDoesNotBrew(names, meta, enzymes)

    def testDoesNotBrewWithoutDate(self):
        names = {'file': 'pass.txt'}
        meta = {'mock': 0}
        enzymes = []
        self.assertDoesNotBrew(names, meta, enzymes)

    def testDoesNotBrewIfDateNotInt(self):
        names = {'file': 'pass.txt'}
        meta = {'date': 'O'}
        enzymes = []
        self.assertDoesNotBrew(names, meta, enzymes)

    def testBrewsIfRaisesEnzymeError(self):
        names = {'file': 'pass.txt'}
        meta = {'date': 0}
        enzymes = [FailMockEnzyme()]
        expected = {}, 'c\n', []
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsWithoutYeast(self):
        names = {'file': 'fail.txt'}
        meta = {'date': 0, 'view_name': 'pass'}
        enzymes = []
        expected = {}, [(0, 'fail.txt', b'type: fail\n...\nc\n')]
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsWithoutYeastIfRaisesEnzymeError(self):
        names = {'file': 'fail.txt'}
        meta = {'date': 0, 'view_name': 'pass'}
        enzymes = [FailMockEnzyme()]
        expected = {}, [(0, 'fail.txt', b'type: fail\n...\nc\n')]
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsIfArchive(self):
        names = {'file': 'mock.zip'}
        meta = {'date': 0}
        enzymes = [self.mock(['pass.txt'])]
        expected = {}, 'c\n', []
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsIfArchiveWithoutYeast(self):
        names = {'file': 'mock.zip'}
        meta = {'date': 0, 'view_name': 'pass'}
        enzymes = [self.mock(['fail.txt'])]
        expected = {}, [(0, 'fail.txt', b'type: fail\n...\nc\n')]
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsIfArchiveWithTwoFilesWithoutYeast(self):
        names = {'file': 'mock.zip'}
        meta = {'date': 0, 'view_name': 'pass'}
        enzymes = [self.mock(['fail.txt', 'wrong-type.txt'])]
        expected = {}, [(0, 'fail.txt', b'type: fail\n...\nc\n'), (0, 'wrong-type.txt', b'type: mock\n...\nc\n')]
        self.assertBrews(names, meta, enzymes, expected)

    def testBrewsIfArchiveWithTwoFilesWithOneYeast(self):
        names = {'file': 'mock.zip'}
        meta = {'date': 0}
        enzymes = [self.mock(['pass.txt', 'fail.txt'])]
        expected = {}, 'c\n', [(0, 'fail.txt', b'type: fail\n...\nc\n')]
        self.assertBrews(names, meta, enzymes, expected)

    def testDoesNotBrewIfArchiveWithTwoYeasts(self):
        names = {'file': 'mock.zip'}
        meta = {'date': 0}
        enzymes = [self.mock(['pass.txt', 'lower-separator.txt'])]
        self.assertDoesNotBrew(names, meta, enzymes)
