import os

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files import File

from beer.tests import IntegrationTestCase

from ...models import FolderAsset, FileAsset
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

    def build(self, name, domain, promote):
        data = {}
        files = {}
        if name is not None:
            files['file'] = self.open(name)
        if domain is not None:
            data['domain'] = domain
        if promote is not None:
            data['promote'] = promote
        return UserForm(data, files)

    def assertValid(self, name, domain, promote, users):
        form = self.build(name, domain, promote)
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.users), len(users))
        for username, defaults in form.users.items():
            user = (username, defaults['email'], defaults['first_name'], defaults['last_name'])
            self.assertIn(user, users)

    def assertNotValid(self, name, domain, promote):
        form = self.build(name, domain, promote)
        self.assertFalse(form.is_valid())

    def testValidWithoutPromote(self):
        self.assertValid('base', self.domain, None, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithFalsePromote(self):
        self.assertValid('base', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithTruePromote(self):
        self.assertValid('base', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

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
        self.assertValid('one', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
        ])

    def testValidForOneUserAndTruePromote(self):
        self.assertValid('one', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
        ])

    def testValidForTwoUsersAndFalsePromote(self):
        self.assertValid('two', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
        ])

    def testValidForTwoUsersAndTruePromote(self):
        self.assertValid('two', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
        ])

    def testValidWithoutFirstLastAndFalsePromote(self):
        self.assertValid('noal', self.domain, False, [
            ('au', 'au@d.com', 'af', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutFirstLastAndTruePromote(self):
        self.assertValid('noal', self.domain, True, [
            ('au', 'au@d.com', 'af', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutSecondLastAndFalsePromote(self):
        self.assertValid('nobl', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutSecondLastAndTruePromote(self):
        self.assertValid('nobl', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutThirdLastAndFalsePromote(self):
        self.assertValid('nocl', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', ''),
        ])

    def testValidWithoutThirdLastAndTruePromote(self):
        self.assertValid('nocl', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', ''),
        ])

    def testValidWithoutFirstFirstAndFalsePromote(self):
        self.assertValid('noaf', self.domain, False, [
            ('au', 'au@d.com', '', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutFirstFirstAndTruePromote(self):
        self.assertValid('noaf', self.domain, True, [
            ('au', 'au@d.com', '', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutSecondFirstAndFalsePromote(self):
        self.assertValid('nobf', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', '', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutSecondFirstAndTruePromote(self):
        self.assertValid('nobf', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', '', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithoutThirdFirstAndFalsePromote(self):
        self.assertValid('nocf', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', '', ''),
        ])

    def testValidWithoutThirdFirstAndTruePromote(self):
        self.assertValid('nocf', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', '', ''),
        ])

    def testNotValidWithFirstAtAndFalsePromote(self):
        self.assertNotValid('noat', self.domain, False)

    def testNotValidWithFirstAtAndTruePromote(self):
        self.assertNotValid('noat', self.domain, True)

    def testNotValidWithSecondAtAndFalsePromote(self):
        self.assertNotValid('nobt', self.domain, False)

    def testNotValidWithSecondAtAndTruePromote(self):
        self.assertNotValid('nobt', self.domain, True)

    def testNotValidWithThirdAtAndFalsePromote(self):
        self.assertNotValid('noct', self.domain, False)

    def testNotValidWithThirdAtAndTruePromote(self):
        self.assertNotValid('noct', self.domain, True)

    def testNotValidWithSameFirstAndFalsePromote(self):
        self.assertNotValid('yesau', self.domain, False)

    def testNotValidWithSameFirstAndTruePromote(self):
        self.assertNotValid('yesau', self.domain, True)

    def testNotValidWithSameSecondAndFalsePromote(self):
        self.assertNotValid('yesbu', self.domain, False)

    def testNotValidWithSameSecondAndTruePromote(self):
        self.assertNotValid('yesbu', self.domain, True)

    def testNotValidWithSameThirdAndFalsePromote(self):
        self.assertNotValid('yescu', self.domain, False)

    def testNotValidWithSameThirdAndTruePromote(self):
        self.assertNotValid('yescu', self.domain, True)

    def testValidWithExtraFirstAndFalsePromote(self):
        self.assertValid('yesam', self.domain, False, [
            ('au', 'au@d.com', 'af', 'am al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithExtraFirstAndTruePromote(self):
        self.assertValid('yesam', self.domain, True, [
            ('au', 'au@d.com', 'af', 'am al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithExtraSecondAndFalsePromote(self):
        self.assertValid('yesbm', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bm bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithExtraSecondAndTruePromote(self):
        self.assertValid('yesbm', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bm bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithExtraThirdAndFalsePromote(self):
        self.assertValid('yescm', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cm cl'),
        ])

    def testValidWithExtraThirdAndTruePromote(self):
        self.assertValid('yescm', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cm cl'),
        ])

    def testValidWithSpaceAndFalsePromote(self):
        self.assertValid('space', self.domain, False, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithSpaceAndTruePromote(self):
        self.assertValid('space', self.domain, True, [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndFalsePromote(self):
        self.assertValid('email', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndTruePromote(self):
        self.assertValid('email', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainForOneUserAndFalsePromote(self):
        self.assertValid('email-one', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
        ])

    def testValidWithEmailWithoutDomainForOneUserAndTruePromote(self):
        self.assertValid('email-one', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
        ])

    def testValidWithEmailWithoutDomainForTwoUsersAndFalsePromote(self):
        self.assertValid('email-two', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
        ])

    def testValidWithEmailWithoutDomainForTwoUsersAndTruePromote(self):
        self.assertValid('email-two', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
        ])

    def testValidWithEmailWithoutDomainAndFirstLastAndFalsePromote(self):
        self.assertValid('email-noal', None, False, [
            ('au', 'ae@ae.com', 'af', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndFirstLastAndTruePromote(self):
        self.assertValid('email-noal', None, True, [
            ('au', 'ae@ae.com', 'af', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndSecondLastAndFalsePromote(self):
        self.assertValid('email-nobl', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndSecondLastAndTruePromote(self):
        self.assertValid('email-nobl', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndThirdLastAndFalsePromote(self):
        self.assertValid('email-nocl', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', ''),
        ])

    def testValidWithEmailWithoutDomainAndThirdLastAndTruePromote(self):
        self.assertValid('email-nocl', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', ''),
        ])

    def testValidWithEmailWithoutDomainAndFirstFirstAndFalsePromote(self):
        self.assertValid('email-noaf', None, False, [
            ('au', 'ae@ae.com', '', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndFirstFirstAndTruePromote(self):
        self.assertValid('email-noaf', None, True, [
            ('au', 'ae@ae.com', '', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndSecondFirstAndFalsePromote(self):
        self.assertValid('email-nobf', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', '', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndSecondFirstAndTruePromote(self):
        self.assertValid('email-nobf', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', '', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailWithoutDomainAndThirdFirstAndFalsePromote(self):
        self.assertValid('email-nocf', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', '', ''),
        ])

    def testValidWithEmailWithoutDomainAndThirdFirstAndTruePromote(self):
        self.assertValid('email-nocf', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', '', ''),
        ])

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

    def testNotValidWithoutFirstAtAndDomainAndFalsePromote(self):
        self.assertNotValid('email-noat', None, False)

    def testNotValidWithoutFirstAtAndDomainAndTruePromote(self):
        self.assertNotValid('email-noat', None, True)

    def testNotValidWithoutSecondAtAndDomainAndFalsePromote(self):
        self.assertNotValid('email-nobt', None, False)

    def testNotValidWithoutSecondAtAndDomainAndTruePromote(self):
        self.assertNotValid('email-nobt', None, True)

    def testNotValidWithoutThirdAtAndDomainAndFalsePromote(self):
        self.assertNotValid('email-noct', None, False)

    def testNotValidWithoutThirdAtAndDomainAndTruePromote(self):
        self.assertNotValid('email-noct', None, True)

    def testNotValidWithEmailAndSameFirstWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yesau', None, False)

    def testNotValidWithEmailAndSameFirstWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yesau', None, True)

    def testNotValidWithEmailAndSameSecondWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yesbu', None, False)

    def testNotValidWithEmailAndSameSecondWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yesbu', None, True)

    def testNotValidWithEmailAndSameThirdWithoutDomainAndFalsePromote(self):
        self.assertNotValid('email-yescu', None, False)

    def testNotValidWithEmailAndSameThirdWithoutDomainAndTruePromote(self):
        self.assertNotValid('email-yescu', None, True)

    def testValidWithEmailAndExtraFirstAndFalsePromote(self):
        self.assertValid('email-yesam', None, False, [
            ('au', 'ae@ae.com', 'af', 'am al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndExtraFirstAndTruePromote(self):
        self.assertValid('email-yesam', None, True, [
            ('au', 'ae@ae.com', 'af', 'am al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndExtraSecondAndFalsePromote(self):
        self.assertValid('email-yesbm', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bm bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndExtraSecondAndTruePromote(self):
        self.assertValid('email-yesbm', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bm bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndExtraThirdAndFalsePromote(self):
        self.assertValid('email-yescm', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cm cl'),
        ])

    def testValidWithEmailAndExtraThirdAndTruePromote(self):
        self.assertValid('email-yescm', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cm cl'),
        ])

    def testValidWithEmailAndSpaceWithoutDomainAndFalsePromote(self):
        self.assertValid('email-space', None, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndSpaceWithoutDomainAndTruePromote(self):
        self.assertValid('email-space', None, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndEmptyDomainAndFalsePromote(self):
        self.assertValid('email', self.empty_domain, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndEmptyDomainAndTruePromote(self):
        self.assertValid('email', self.empty_domain, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndWhiteDomainAndFalsePromote(self):
        self.assertValid('email', self.white_domain, False, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])

    def testValidWithEmailAndWhiteDomainAndTruePromote(self):
        self.assertValid('email', self.white_domain, True, [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ])


class AssetFormTests:
    name = 'n'
    child_name = 'cn'
    other_name = 'on'
    empty_name = ''
    white_name = ' \t\n'
    slash_name = 'n/n'

    def setUp(self):
        self.upper_name = (self.Asset.name.field.max_length + 1) * 'n'

    def isValid(self, name, edit):
        user = User.objects.create_user('u')
        grand_parent = FolderAsset.objects.create(user=user, parent=None, name='gpn')
        parent = FolderAsset.objects.create(user=user, parent=grand_parent, name='pn')
        child = self.Asset.objects.create(user=user, parent=parent, name=self.child_name)
        self.Asset.objects.create(user=user, parent=parent, name=self.other_name)
        data = {}
        if name is not None:
            data['name'] = name
        kwargs = {
            'Asset': self.Asset,
            'user': user,
            'parent': parent,
        }
        if edit:
            kwargs['child'] = child
        else:
            kwargs['child'] = None
        form = AssetForm(data, **kwargs)
        return form.is_valid()

    def assertValid(self, name, edit):
        self.assertTrue(self.isValid(name, edit))

    def assertNotValid(self, name, edit):
        self.assertFalse(self.isValid(name, edit))

    def testValidWithFalseEdit(self):
        self.assertValid(self.name, False)

    def testValidWithTrueEdit(self):
        self.assertValid(self.name, True)

    def testNotValidWithoutNameAndFalseEdit(self):
        self.assertNotValid(None, False)

    def testNotValidWithoutNameAndTrueEdit(self):
        self.assertNotValid(None, True)

    def testNotValidWithOwnNameAndFalseEdit(self):
        self.assertNotValid(self.child_name, False)

    def testValidWithOwnNameAndTrueEdit(self):
        self.assertValid(self.child_name, True)

    def testNotValidWithSameNameAndFalseEdit(self):
        self.assertNotValid(self.other_name, False)

    def testNotValidWithSameNameAndTrueEdit(self):
        self.assertNotValid(self.other_name, True)

    def testNotValidWithEmptyNameAndFalseEdit(self):
        self.assertNotValid(self.empty_name, False)

    def testNotValidWithEmptyNameAndTrueEdit(self):
        self.assertNotValid(self.empty_name, True)

    def testNotValidWithWhiteNameAndFalseEdit(self):
        self.assertNotValid(self.white_name, False)

    def testNotValidWithWhiteNameAndTrueEdit(self):
        self.assertNotValid(self.white_name, True)

    def testNotValidWithSlashNameAndFalseEdit(self):
        self.assertNotValid(self.slash_name, False)

    def testNotValidWithSlashNameAndTrueEdit(self):
        self.assertNotValid(self.slash_name, True)

    def testNotValidWithUpperNameAndFalseEdit(self):
        self.assertNotValid(self.upper_name, False)

    def testNotValidWithUpperNameAndTrueEdit(self):
        self.assertNotValid(self.upper_name, True)


class FolderAssetFormTests(AssetFormTests, IntegrationTestCase):
    Asset = FolderAsset


class FileAssetFormTests(AssetFormTests, IntegrationTestCase):
    Asset = FileAsset
