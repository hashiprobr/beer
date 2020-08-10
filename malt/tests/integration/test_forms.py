import os

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files import File

from beer.tests import IntegrationTestCase

from ...models import Asset, FolderAsset, FileAsset
from ...forms import UserForm, AssetForm

User = get_user_model()


class UserFormTests(IntegrationTestCase):
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
        form = UserForm(data, files)
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

    def testNotValidWithFirstEmailAndFalsePromote(self):
        self.assertNotValid('noae', self.domain, False)

    def testNotValidWithFirstEmailAndTruePromote(self):
        self.assertNotValid('noae', self.domain, True)

    def testNotValidWithSecondEmailAndFalsePromote(self):
        self.assertNotValid('nobe', self.domain, False)

    def testNotValidWithSecondEmailAndTruePromote(self):
        self.assertNotValid('nobe', self.domain, True)

    def testNotValidWithThirdEmailAndFalsePromote(self):
        self.assertNotValid('noce', self.domain, False)

    def testNotValidWithThirdEmailAndTruePromote(self):
        self.assertNotValid('noce', self.domain, True)

    def testNotValidWithSameFirstAndFalsePromote(self):
        self.assertNotValid('yesa', self.domain, False)

    def testNotValidWithSameFirstAndTruePromote(self):
        self.assertNotValid('yesa', self.domain, True)

    def testNotValidWithSameSecondAndFalsePromote(self):
        self.assertNotValid('yesb', self.domain, False)

    def testNotValidWithSameSecondAndTruePromote(self):
        self.assertNotValid('yesb', self.domain, True)

    def testNotValidWithSameThirdAndFalsePromote(self):
        self.assertNotValid('yesc', self.domain, False)

    def testNotValidWithSameThirdAndTruePromote(self):
        self.assertNotValid('yesc', self.domain, True)

    def testValidWithSpaceAndFalsePromote(self):
        self.assertValid('space', self.domain, False)

    def testValidWithSpaceAndTruePromote(self):
        self.assertValid('space', self.domain, True)

    def testValidWithExtraAndFalsePromote(self):
        self.assertValid('extra', self.domain, False)

    def testValidWithExtraAndTruePromote(self):
        self.assertValid('extra', self.domain, True)

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

    def testNotValidWithoutFirstEmailAndDomainAndFalsePromote(self):
        self.assertNotValid('email-noae', None, False)

    def testNotValidWithoutFirstEmailAndDomainAndTruePromote(self):
        self.assertNotValid('email-noae', None, True)

    def testNotValidWithoutSecondEmailAndDomainAndFalsePromote(self):
        self.assertNotValid('email-nobe', None, False)

    def testNotValidWithoutSecondEmailAndDomainAndTruePromote(self):
        self.assertNotValid('email-nobe', None, True)

    def testNotValidWithoutThirdEmailAndDomainAndFalsePromote(self):
        self.assertNotValid('email-noce', None, False)

    def testNotValidWithoutThirdEmailAndDomainAndTruePromote(self):
        self.assertNotValid('email-noce', None, True)

    def testNotValidWithEmailAndSameFirstWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yesa', None, False)

    def testNotValidWithEmailAndSameFirstWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yesa', None, True)

    def testNotValidWithEmailAndSameSecondWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yesb', None, False)

    def testNotValidWithEmailAndSameSecondWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yesb', None, True)

    def testNotValidWithEmailAndSameThirdWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yesc', None, False)

    def testNotValidWithEmailAndSameThirdWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yesc', None, True)

    def testValidWithEmailAndSpaceWithoutDomainAndFalsePromote(self):
        self.assertValid('email-space', None, False)

    def testValidWithEmailAndSpaceWithoutDomainAndTruePromote(self):
        self.assertValid('email-space', None, True)

    def testValidWithEmailAndExtraWithoutDomainAndFalsePromote(self):
        self.assertValid('email-extra', None, False)

    def testValidWithEmailAndExtraWithoutDomainAndTruePromote(self):
        self.assertValid('email-extra', None, True)

    def testValidWithEmailAndEmptyDomainAndFalsePromote(self):
        self.assertValid('email', self.empty_domain, False)

    def testValidWithEmailAndEmptyDomainAndTruePromote(self):
        self.assertValid('email', self.empty_domain, True)

    def testValidWithEmailAndWhiteDomainAndFalsePromote(self):
        self.assertValid('email', self.white_domain, False)

    def testValidWithEmailAndWhiteDomainAndTruePromote(self):
        self.assertValid('email', self.white_domain, True)


class AssetFormTests(IntegrationTestCase):
    name = 'n'
    other_name = 'on'
    empty_name = ''
    white_name = ' \t\n'
    upper_name = (Asset.name.field.max_length + 1) * 'n'

    def isValid(self, name, Asset, edit):
        user = User.objects.create_user('u')
        parent = FolderAsset.objects.create(user=user, parent=None, name='p')
        child = Asset.objects.create(user=user, parent=parent, name=self.other_name)
        data = {}
        if name is not None:
            data['name'] = name
        kwargs = {
            'Asset': Asset,
            'user': user,
            'parent': parent,
        }
        if edit:
            kwargs['child'] = child
        else:
            kwargs['child'] = None
        form = AssetForm(data, **kwargs)
        return form.is_valid()

    def assertValid(self, name, Asset, new):
        self.assertTrue(self.isValid(name, Asset, new))

    def assertNotValid(self, name, Asset, new):
        self.assertFalse(self.isValid(name, Asset, new))

    def testValidWithFolderAsset(self):
        self.assertValid(self.name, FolderAsset, False)

    def testValidWithFileAsset(self):
        self.assertValid(self.name, FileAsset, False)

    def testNotValidWithoutNameWithFolderAsset(self):
        self.assertNotValid(None, FolderAsset, False)

    def testNotValidWithoutNameWithFileAsset(self):
        self.assertNotValid(None, FileAsset, False)

    def testNotValidWithEmptyNameWithFolderAsset(self):
        self.assertNotValid(self.empty_name, FolderAsset, False)

    def testNotValidWithEmptyNameWithFileAsset(self):
        self.assertNotValid(self.empty_name, FileAsset, False)

    def testNotValidWithWhiteNameWithFolderAsset(self):
        self.assertNotValid(self.white_name, FolderAsset, False)

    def testNotValidWithWhiteNameWithFileAsset(self):
        self.assertNotValid(self.white_name, FileAsset, False)

    def testNotValidWithUpperNameWithFolderAsset(self):
        self.assertNotValid(self.upper_name, FolderAsset, False)

    def testNotValidWithUpperNameWithFileAsset(self):
        self.assertNotValid(self.upper_name, FileAsset, False)

    def testNotValidWithSameNameWithFolderAsset(self):
        self.assertNotValid(self.other_name, FolderAsset, False)

    def testNotValidWithSameNameWithFileAsset(self):
        self.assertNotValid(self.other_name, FileAsset, False)

    def testNotValidWithSameNameButEditWithFolderAsset(self):
        self.assertValid(self.other_name, FolderAsset, True)

    def testNotValidWithSameNameButEditWithFileAsset(self):
        self.assertValid(self.other_name, FileAsset, True)
