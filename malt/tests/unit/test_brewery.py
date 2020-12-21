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

    def testGrowsWithExtraSpaces(self):
        self.assertGrows('extra-spaces.txt', ' \t\n \tc \t\n \t\n')

    def testGrowsWithExtraSeparators(self):
        self.assertGrows('extra-separators.txt', '...\nc\n...\n')

    def testDoesNotGrowWithoutSeparators(self):
        self.assertDoesNotGrow('no-separators.txt')

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

    def testDoesNotGrowIfCleanRaisesYeastError(self):
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


class BreweryTests(BrewingTests, UnitTestCase):
    def mock(self, contents):
        return PassMockEnzyme([(0, name, content) for name, content in contents.items()])

    def brew(self, contents, meta, enzymes, MockPrimer):
        brewery = Brewery()
        files = MultiValueDict()
        for name, content in contents.items():
            files[name] = File(BytesIO(content))
        brewery.brew(files, meta, enzymes, self.MockYeasts, MockGrower, MockPrimer)

    def assertBrews(self, contents, meta, enzymes, MockPrimer):
        try:
            self.brew(contents, meta, enzymes, MockPrimer)
        except BrewError:
            self.fail('BrewError raised')

    def assertDoesNotBrew(self, contents, meta, enzymes, MockPrimer):
        with self.assertRaises(BrewError):
            self.brew(contents, meta, enzymes, MockPrimer)

    def testBrews(self):
        contents = {'file': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testBrewsIfConvertsRaiseEnzymeError(self):
        contents = {'file': b'pass-pass'}
        meta = {'date': 0}
        enzymes = [FailMockEnzyme()]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewWithoutFile(self):
        contents = {}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewWithTwoFiles(self):
        contents = {'file': b'pass-pass', 'mock': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfInputNotFile(self):
        contents = {'mock': b'pass-pass'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewWithoutDate(self):
        contents = {'file': b'pass-pass'}
        meta = {'mock': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfDateNotInt(self):
        contents = {'file': b'pass-pass'}
        meta = {'date': 'O'}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfFermentRaisesBrewError(self):
        contents = {'file': b'pass-fail'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testBrewsWithoutYeast(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testBrewsWithoutYeastIfConvertsRaiseEnzymeError(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [FailMockEnzyme()]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewWithoutYeastIfPrimeRaisesBrewError(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = []
        MockPrimer = FailMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testBrewsIfArchive(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'file': b'pass-pass'})]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfArchiveAndFermentRaisesBrewError(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'file': b'pass-fail'})]
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testBrewsIfArchiveWithoutYeast(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock'})]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfArchiveWithoutYeastAndPrimeRaisesBrewError(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock'})]
        MockPrimer = FailMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)

    def testBrewsIfArchiveWithTwoFilesWithoutYeast(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock', 'b': b'mock'})]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testBrewsIfArchiveWithTwoFilesButOneYeast(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'mock', 'b': b'pass-pass'})]
        MockPrimer = PassMockPrimer
        self.assertBrews(contents, meta, enzymes, MockPrimer)

    def testDoesNotBrewIfArchiveWithTwoYeasts(self):
        contents = {'file': b'mock'}
        meta = {'date': 0}
        enzymes = [self.mock({'a': b'pass-pass', 'b': b'pass-pass'})]
        MockPrimer = PassMockPrimer
        self.assertDoesNotBrew(contents, meta, enzymes, MockPrimer)
