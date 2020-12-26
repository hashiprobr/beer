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

    def assertDoesNotConvertContent(self, content):
        with self.assertRaises(EnzymeError):
            self.enzyme.convert(content)

    def assertDoesNotConvertFile(self, name):
        content = self.openFile(name)
        self.assertDoesNotConvertContent(content)

    def assertConvertsArchives(self, name, expected):
        for content in self.openArchives(name):
            actual = [(member[1], member[2]) for member in self.enzyme.convert(content)]
            self.assertEqual(len(expected), len(actual))
            for expected_path, (actual_path, actual_content) in zip(sorted(expected), sorted(actual)):
                self.assertEqual(expected_path, actual_path)
                expected_name = os.path.basename(expected_path)
                expected_content = self.openFile(expected_name)
                self.assertEqual(expected_content, actual_content)

    def assertDoesNotConvertArchives(self, name):
        for content in self.openArchives(name):
            self.assertDoesNotConvertContent(content)

    def testDoesNotConvertEmptyFile(self):
        self.assertDoesNotConvertFile('empty_file')

    def testDoesNotConvertBinaryFile(self):
        self.assertDoesNotConvertFile('file.bin')

    def testDoesNotConvertTextFile(self):
        self.assertDoesNotConvertFile('file.txt')

    def testDoesNotConvertBombArchives(self):
        self.assertDoesNotConvertArchives('bomb')

    def testConvertsArchivesWithZeroLevels(self):
        self.assertConvertsArchives('zero', [
        ])

    def testConvertsArchivesWithOneLevel(self):
        self.assertConvertsArchives('one', [
            'empty_file',
            'file.bin',
            'file.txt',
        ])

    def testConvertsArchivesWithTwoLevels(self):
        self.assertConvertsArchives('two', [
            'folder/empty_file',
            'folder/file.bin',
            'folder/file.txt',
            'empty_file',
            'file.bin',
            'file.txt',
        ])

    def testConvertsArchivesWithThreeLevels(self):
        self.assertConvertsArchives('three', [
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
