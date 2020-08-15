import os

from io import BytesIO

from django.core.files import File
from django.utils.datastructures import MultiValueDict

from beer.tests import UnitTestCase

from ...brewing import BrewError, YeastError, Brewer, Yeast
from ...enzymes import EnzymeError, Enzyme
from ...brewery import Grower, Primer, Brewery


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


class PassFailMockYeast(PassMockYeast):
    def ferment(self, meta, data, sugars):
        self.exit('mock')

    def referment(self, meta, sugars):
        self.exit('mock')


class PassPassMockYeast(PassMockYeast):
    def ferment(self, meta, data, sugars):
        return None

    def referment(self, meta, sugars):
        return None


class BrewingTests:
    MockYeasts = {
        'fail': FailMockYeast,
        'pass': PassMockYeast,
        'pass-fail': PassFailMockYeast,
        'pass-pass': PassPassMockYeast,
    }


class GrowerTests(BrewingTests, UnitTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def open(self, name):
        path = os.path.join(self.dir, name)
        with open(path, 'rb') as file:
            content = file.read()
        return content

    def grow(self, name):
        grower = Grower()
        return grower.grow(self.open(name), self.MockYeasts)

    def assertGrows(self, name, expected):
        yeast, meta, actual = self.grow(name)
        self.assertIsInstance(yeast, self.MockYeasts['pass'])
        self.assertEqual({}, meta)
        self.assertEqual(expected, actual)

    def assertDoesNotGrow(self, name):
        self.assertIsNone(self.grow(name))

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


class PrimerTests(BrewingTests, UnitTestCase):
    def prime(self, meta):
        primer = Primer()
        primer.prime(meta, None, self.MockYeasts)

    def assertPrimes(self, meta):
        try:
            self.prime(meta)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotPrime(self, meta):
        with self.assertRaises(BrewError):
            self.prime(meta)

    def testPrimes(self):
        self.assertPrimes({'view_name': 'pass-pass'})

    def testDoesNotPrimeWithoutType(self):
        self.assertDoesNotPrime({'mock': 'pass-pass'})

    def testDoesNotPrimeWithWrongType(self):
        self.assertDoesNotPrime({'view_name': 'mock'})

    def testDoesNotPrimeIfCleanRaisesYeastError(self):
        self.assertDoesNotPrime({'view_name': 'fail'})

    def testDoesNotPrimeIfRefermentRaisesBrewError(self):
        self.assertDoesNotPrime({'view_name': 'pass-fail'})


class MockGrower(Brewer):
    def grow(self, content, Yeasts):
        try:
            Yeast = Yeasts[content.decode('utf-8')]
        except KeyError:
            return None
        return Yeast(), None, None


class FailMockPrimer(Brewer):
    def prime(self, meta, sugars, Yeasts):
        self.exit('mock')


class PassMockPrimer(Brewer):
    def prime(self, meta, sugars, Yeasts):
        return None


class BreweryTests(BrewingTests, UnitTestCase):
    def mock(self, contents):
        return PassMockEnzyme([(0, name, content) for name, content in contents.items()])

    def brew(self, contents, meta, enzymes, Primer):
        brewery = Brewery()
        files = MultiValueDict()
        for name, content in contents.items():
            files[name] = File(BytesIO(content))
        brewery.brew(files, meta, enzymes, self.MockYeasts, MockGrower, Primer)

    def assertBrews(self, names, meta, enzymes, Primer):
        try:
            self.brew(names, meta, enzymes, Primer)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotBrew(self, names, meta, enzymes, Primer):
        with self.assertRaises(BrewError):
            self.brew(names, meta, enzymes, Primer)

    def testBrews(self):
        names = {'file': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testBrewsIfRaisesEnzymeError(self):
        names = {'file': b'pass-pass'}
        meta = {'date': 0}
        enzymes = [FailMockEnzyme()]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testDoesNotBrewWithoutFile(self):
        names = {}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewWithTwoFiles(self):
        names = {'file': b'pass-pass', 'mock': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewIfInputNotFile(self):
        names = {'mock': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewWithoutDate(self):
        names = {'file': b'pass-pass'}
        meta = {'mock': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewIfDateNotInt(self):
        names = {'file': b'pass-pass'}
        meta = {'date': 'O'}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewIfFermentRaisesBrewError(self):
        names = {'file': b'pass-fail'}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testBrewsWithoutYeast(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = []
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testBrewsWithoutYeastIfRaisesEnzymeError(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [FailMockEnzyme()]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testDoesNotBrewWithoutYeastIfPrimerRaisesBrewError(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = []
        Primer = FailMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testBrewsIfArchive(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'file': b'pass-pass'})]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testBrewsIfArchiveWithoutYeast(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock'})]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testDoesNotBrewIfArchiveAndFermentRaisesBrewError(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'file': b'pass-fail'})]
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testDoesNotBrewIfArchiveWithoutYeastAndPrimerRaisesBrewError(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock'})]
        Primer = FailMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)

    def testBrewsIfArchiveWithTwoFilesWithoutYeast(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock', 'b': b'mock'})]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testBrewsIfArchiveWithTwoFilesButOneYeast(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock', 'b': b'pass-pass'})]
        Primer = PassMockPrimer
        self.assertBrews(names, meta, enzymes, Primer)

    def testDoesNotBrewIfArchiveWithTwoYeasts(self):
        names = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'pass-pass', 'b': b'pass-pass'})]
        Primer = PassMockPrimer
        self.assertDoesNotBrew(names, meta, enzymes, Primer)
