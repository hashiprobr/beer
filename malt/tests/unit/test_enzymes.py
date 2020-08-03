import os

from beer.tests import UnitTestCase

from ...enzymes import EnzymeError, ZipEnzyme, TarEnzyme


class EnzymeTests:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def openFile(self, name):
        path = os.path.join(self.dir, name)
        with open(path, 'rb') as file:
            content = file.read()
        return content

    def openArchives(self, name):
        for extension in self.extensions:
            yield self.openFile('{}.{}'.format(name, extension))

    def assertRaisesEnzymeErrorWithFile(self, name):
        content = self.openFile(name)
        with self.assertRaises(EnzymeError):
            self.enzyme.convert(content)

    def assertRaisesEnzymeErrorWithArchives(self, name):
        for content in self.openArchives(name):
            with self.assertRaises(EnzymeError):
                self.enzyme.convert(content)

    def assertConverts(self, name, expected):
        for content in self.openArchives(name):
            actual = [member[1] for member in self.enzyme.convert(content)]
            self.assertEqual(len(expected), len(actual))
            for expected_name, actual_name in zip(sorted(expected), sorted(actual)):
                self.assertEqual(expected_name, actual_name)

    def testRaisesEnzymeErrorWithEmptyFile(self):
        self.assertRaisesEnzymeErrorWithFile('empty_file')

    def testRaisesEnzymeErrorWithBinaryFile(self):
        self.assertRaisesEnzymeErrorWithFile('file.bin')

    def testRaisesEnzymeErrorWithTextFile(self):
        self.assertRaisesEnzymeErrorWithFile('file.txt')

    def testRaisesEnzymeErrorWithBombArchives(self):
        self.assertRaisesEnzymeErrorWithArchives('bomb')

    def testConvertsWithEmptyFile(self):
        self.assertConverts('empty', ['empty_file'])

    def testConvertsWithBinaryFile(self):
        self.assertConverts('binary', ['file.bin'])

    def testConvertsWithTextFile(self):
        self.assertConverts('text', ['file.txt'])

    def testConvertsWithZeroLevels(self):
        self.assertConverts('zero', [])

    def testConvertsWithOneLevel(self):
        self.assertConverts('one', [
            'empty_file',
            'file.bin',
            'file.txt',
        ])

    def testConvertsWithTwoLevels(self):
        self.assertConverts('two', [
            'folder/empty_file',
            'folder/file.bin',
            'folder/file.txt',
            'empty_file',
            'file.bin',
            'file.txt',
        ])

    def testConvertsWithThreeLevels(self):
        self.assertConverts('three', [
            'folder/folder/empty_file',
            'folder/folder/file.bin',
            'folder/folder/file.txt',
            'folder/empty_file',
            'folder/file.bin',
            'folder/file.txt',
            'empty_file',
            'file.bin',
            'file.txt',
        ])


class ZipEnzymeTests(EnzymeTests, UnitTestCase):
    enzyme = ZipEnzyme()
    extensions = ['zip']


class TarEnzymeTests(EnzymeTests, UnitTestCase):
    enzyme = TarEnzyme()
    extensions = ['tar', 'tar.gz', 'tar.bz2']
