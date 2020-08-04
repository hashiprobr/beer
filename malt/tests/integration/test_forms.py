import os

from io import BytesIO

from django.core.files import File

from beer.tests import IntegrationTestCase

from ...forms import UserAddForm


class UserAddFormTests(IntegrationTestCase):
    domain = 'd.com'
    empty_domain = ''
    white_domain = ' \t\n'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def open(self, name):
        path = os.path.join(self.dir, name + '.txt')
        with open(path, 'rb') as file:
            content = file.read()
        return File(BytesIO(content), name)

    def isValid(self, name, domain, promote):
        data = {}
        files = {}
        if name is not None:
            files['file'] = self.open(name)
        if domain is not None:
            data['domain'] = domain
        if promote is not None:
            data['promote'] = promote
        form = UserAddForm(data, files)
        return form.is_valid()

    def assertValid(self, name, domain, promote):
        self.assertTrue(self.isValid(name, domain, promote))

    def assertNotValid(self, name, domain, promote):
        self.assertFalse(self.isValid(name, domain, promote))

    def testValidWithoutPromote(self):
        self.assertValid('base', self.domain, None)

    def testValidWithFalsePromote(self):
        self.assertValid('base', self.domain, False)

    def testValidWithTruePromote(self):
        self.assertValid('base', self.domain, True)

    def testNotValidWithoutFileAndFalsePromote(self):
        self.assertNotValid(None, self.domain, False)

    def testNotValidWithoutFileAndTruePromote(self):
        self.assertNotValid(None, self.domain, True)

    def testNotValidWithEmptyFileAndFalsePromote(self):
        self.assertNotValid('empty', self.domain, False)

    def testNotValidWithEmptyFileAndTruePromote(self):
        self.assertNotValid('empty', self.domain, True)

    def testNotValidWithWhiteFileAndFalsePromote(self):
        self.assertNotValid('white', self.domain, False)

    def testNotValidWithWhiteFileAndTruePromote(self):
        self.assertNotValid('white', self.domain, True)

    def testNotValidWithBinaryFileAndFalsePromote(self):
        self.assertNotValid('binary', self.domain, False)

    def testNotValidWithBinaryFileAndTruePromote(self):
        self.assertNotValid('binary', self.domain, True)

    def testValidForOneUserAndFalsePromote(self):
        self.assertValid('one', self.domain, False)

    def testValidForOneUserAndTruePromote(self):
        self.assertValid('one', self.domain, True)

    def testValidForTwoUsersAndFalsePromote(self):
        self.assertValid('two', self.domain, False)

    def testValidForTwoUsersAndTruePromote(self):
        self.assertValid('two', self.domain, True)

    def testValidWithoutFirstLastAndFalsePromote(self):
        self.assertValid('noal', self.domain, False)

    def testValidWithoutFirstLastAndTruePromote(self):
        self.assertValid('noal', self.domain, True)

    def testValidWithoutSecondLastAndFalsePromote(self):
        self.assertValid('nobl', self.domain, False)

    def testValidWithoutSecondLastAndTruePromote(self):
        self.assertValid('nobl', self.domain, True)

    def testValidWithoutThirdLastAndFalsePromote(self):
        self.assertValid('nocl', self.domain, False)

    def testValidWithoutThirdLastAndTruePromote(self):
        self.assertValid('nocl', self.domain, True)

    def testNotValidWithoutFirstFirstAndFalsePromote(self):
        self.assertNotValid('noaf', self.domain, False)

    def testNotValidWithoutFirstFirstAndTruePromote(self):
        self.assertNotValid('noaf', self.domain, True)

    def testNotValidWithoutSecondFirstAndFalsePromote(self):
        self.assertNotValid('nobf', self.domain, False)

    def testNotValidWithoutSecondFirstAndTruePromote(self):
        self.assertNotValid('nobf', self.domain, True)

    def testNotValidWithoutThirdFirstAndFalsePromote(self):
        self.assertNotValid('nocf', self.domain, False)

    def testNotValidWithoutThirdFirstAndTruePromote(self):
        self.assertNotValid('nocf', self.domain, True)

    def testValidWithSpaceAndFalsePromote(self):
        self.assertValid('space', self.domain, False)

    def testValidWithSpaceAndTruePromote(self):
        self.assertValid('space', self.domain, True)

    def testNotValidWithEmailAndFalsePromote(self):
        self.assertNotValid('email', self.domain, False)

    def testNotValidWithEmailAndTruePromote(self):
        self.assertNotValid('email', self.domain, True)

    def testValidWithEmailWithoutDomainAndFalsePromote(self):
        self.assertValid('email', None, False)

    def testValidWithEmailWithoutDomainAndTruePromote(self):
        self.assertValid('email', None, True)

    def testValidWithEmailWithoutDomainForOneUserAndFalsePromote(self):
        self.assertValid('email-one', None, False)

    def testValidWithEmailWithoutDomainForOneUserAndTruePromote(self):
        self.assertValid('email-one', None, True)

    def testValidWithEmailWithoutDomainForTwoUsersAndFalsePromote(self):
        self.assertValid('email-two', None, False)

    def testValidWithEmailWithoutDomainForTwoUsersAndTruePromote(self):
        self.assertValid('email-two', None, True)

    def testValidWithEmailWithoutDomainAndFirstLastAndFalsePromote(self):
        self.assertValid('email-noal', None, False)

    def testValidWithEmailWithoutDomainAndFirstLastAndTruePromote(self):
        self.assertValid('email-noal', None, True)

    def testValidWithEmailWithoutDomainAndSecondLastAndFalsePromote(self):
        self.assertValid('email-nobl', None, False)

    def testValidWithEmailWithoutDomainAndSecondLastAndTruePromote(self):
        self.assertValid('email-nobl', None, True)

    def testValidWithEmailWithoutDomainAndThirdLastAndFalsePromote(self):
        self.assertValid('email-nocl', None, False)

    def testValidWithEmailWithoutDomainAndThirdLastAndTruePromote(self):
        self.assertValid('email-nocl', None, True)

    def testNotValidWithEmailWithoutDomainAndFirstFirstAndFalsePromote(self):
        self.assertNotValid('email-noaf', None, False)

    def testNotValidWithEmailWithoutDomainAndFirstFirstAndTruePromote(self):
        self.assertNotValid('email-noaf', None, True)

    def testNotValidWithEmailWithoutDomainAndSecondFirstAndFalsePromote(self):
        self.assertNotValid('email-nobf', None, False)

    def testNotValidWithEmailWithoutDomainAndSecondFirstAndTruePromote(self):
        self.assertNotValid('email-nobf', None, True)

    def testNotValidWithEmailWithoutDomainAndThirdFirstAndFalsePromote(self):
        self.assertNotValid('email-nocf', None, False)

    def testNotValidWithEmailWithoutDomainAndThirdFirstAndTruePromote(self):
        self.assertNotValid('email-nocf', None, True)

    def testValidWithEmailAndSpaceWithoutDomainAndFalsePromote(self):
        self.assertValid('email-space', None, False)

    def testValidWithEmailAndSpaceWithoutDomainAndTruePromote(self):
        self.assertValid('email-space', None, True)

    def testValidWithEmailAndEmptyDomainAndFalsePromote(self):
        self.assertValid('email', self.empty_domain, False)

    def testValidWithEmailAndEmptyDomainAndTruePromote(self):
        self.assertValid('email', self.empty_domain, True)

    def testValidWithEmailAndWhiteDomainAndFalsePromote(self):
        self.assertValid('email', self.white_domain, False)

    def testValidWithEmailAndWhiteDomainAndTruePromote(self):
        self.assertValid('email', self.white_domain, True)
