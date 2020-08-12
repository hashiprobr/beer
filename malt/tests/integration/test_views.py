import os

from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model

from beer import public_storage
from beer.tests import ViewTestCase

from ...models import PowerUser, Asset, FolderAsset, FileAsset
from ...caches import power_cache
from ...views import PAGE_SIZE, CSRF_KEY

User = get_user_model()


class UserViewTests:
    super_username = '35fde5760c42b7bc'
    username = '528070b65f32f4f7'
    other_username = 'bba8253c7b9a27d2'

    super_password = 'sp'
    password = 'p'

    email = 'e@e.com'
    other_email = 'oe@oe.com'

    first_name = 'f'
    other_first_name = 'of'

    last_name = 'l'
    other_last_name = 'ol'

    def setUp(self):
        User.objects.create_superuser(self.super_username, password=self.super_password)
        self.user = User.objects.create_user(self.username, password=self.password)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def kwargs(self):
        return None

    def power(self):
        return PowerUser.objects.filter(user=self.user).exists()

    def assertPower(self):
        self.assertTrue(self.power())
        self.assertTrue(power_cache.get(self.user))

    def assertNotPower(self):
        self.assertFalse(self.power())
        self.assertFalse(power_cache.get(self.user))

    def testGetRedirects(self):
        self.assertEqual(302, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testPostRedirects(self):
        self.assertEqual(302, self.post_status(kwargs=self.kwargs()))

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.post_status(kwargs=self.kwargs()))


class UserManageViewTests(UserViewTests, ViewTestCase):
    view_name = 'user_manage'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def open(self, name):
        path = os.path.join(self.dir, name + '.txt')
        with open(path, 'rb') as file:
            content = file.read()
        return BytesIO(content)

    def assertGet(self, n, page, length, left, center, right):
        for i in range(n - 2):
            User.objects.create_user('{}{}'.format(self.username, i))
        self.superLogin()
        if page is None:
            html = self.get_html()
        else:
            html = self.get_html(query=[('page', page)])
        trs = html.select('tbody tr')
        caption = html.select_one('caption')
        arrows = [self.string(a) for a in caption.select('a')]
        self.assertEqual(length, len(trs))
        self.assertEqual(left, '🡨' in arrows)
        self.assertIn(center, self.string(caption))
        self.assertEqual(right, '🡪' in arrows)

    def assertPost(self, name, domain, promote, expected):
        self.superLogin()
        data = {
            'file': self.open(name),
            'promote': promote,
        }
        if domain is not None:
            data['domain'] = domain
        self.post(data=data)
        for values in expected:
            user = User.objects.get(username=values[0], email=values[1], first_name=values[2], last_name=values[3])
            self.assertEqual(promote, PowerUser.objects.filter(user=user).exists())

    def testPageSize(self):
        self.assertLessEqual(4, PAGE_SIZE)

    def testGetForHalfPageWithoutPage(self):
        self.assertGet(PAGE_SIZE // 2, None, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetForHalfPageWithPageOne(self):
        self.assertGet(PAGE_SIZE // 2, 1, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetForHalfPageWithPageTwo(self):
        self.assertGet(PAGE_SIZE // 2, 2, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetForOnePageWithoutPage(self):
        self.assertGet(PAGE_SIZE, None, PAGE_SIZE, False, '1 of 1', False)

    def testGetForOnePageWithPageOne(self):
        self.assertGet(PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 1', False)

    def testGetForOnePageWithPageTwo(self):
        self.assertGet(PAGE_SIZE, 2, PAGE_SIZE, False, '1 of 1', False)

    def testGetForOneHalfPageWithoutPage(self):
        self.assertGet(3 * PAGE_SIZE // 2, None, PAGE_SIZE, False, '1 of 2', True)

    def testGetForOneHalfPageWithPageOne(self):
        self.assertGet(3 * PAGE_SIZE // 2, 1, PAGE_SIZE, False, '1 of 2', True)

    def testGetForOneHalfPageWithPageTwo(self):
        self.assertGet(3 * PAGE_SIZE // 2, 2, PAGE_SIZE // 2, True, '2 of 2', False)

    def testGetForOneHalfPageWithPageThree(self):
        self.assertGet(3 * PAGE_SIZE // 2, 3, PAGE_SIZE, False, '1 of 2', True)

    def testGetForTwoPagesWithoutPage(self):
        self.assertGet(2 * PAGE_SIZE, None, PAGE_SIZE, False, '1 of 2', True)

    def testGetForTwoPagesWithPageOne(self):
        self.assertGet(2 * PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 2', True)

    def testGetForTwoPagesWithPageTwo(self):
        self.assertGet(2 * PAGE_SIZE, 2, PAGE_SIZE, True, '2 of 2', False)

    def testGetForTwoPagesWithPageThree(self):
        self.assertGet(2 * PAGE_SIZE, 3, PAGE_SIZE, False, '1 of 2', True)

    def testGetForTwoHalfPagesWithoutPage(self):
        self.assertGet(5 * PAGE_SIZE // 2, None, PAGE_SIZE, False, '1 of 3', True)

    def testGetForTwoHalfPagesWithPageOne(self):
        self.assertGet(5 * PAGE_SIZE // 2, 1, PAGE_SIZE, False, '1 of 3', True)

    def testGetForTwoHalfPagesWithPageTwo(self):
        self.assertGet(5 * PAGE_SIZE // 2, 2, PAGE_SIZE, True, '2 of 3', True)

    def testGetForTwoHalfPagesWithPageThree(self):
        self.assertGet(5 * PAGE_SIZE // 2, 3, PAGE_SIZE // 2, True, '3 of 3', False)

    def testGetForTwoHalfPagesWithPageFour(self):
        self.assertGet(5 * PAGE_SIZE // 2, 4, PAGE_SIZE, False, '1 of 3', True)

    def testGetForThreePagesWithoutPage(self):
        self.assertGet(3 * PAGE_SIZE, None, PAGE_SIZE, False, '1 of 3', True)

    def testGetForThreePagesWithPageOne(self):
        self.assertGet(3 * PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 3', True)

    def testGetForThreePagesWithPageTwo(self):
        self.assertGet(3 * PAGE_SIZE, 2, PAGE_SIZE, True, '2 of 3', True)

    def testGetForThreePagesWithPageThree(self):
        self.assertGet(3 * PAGE_SIZE, 3, PAGE_SIZE, True, '3 of 3', False)

    def testGetForThreePagesWithPageFour(self):
        self.assertGet(3 * PAGE_SIZE, 4, PAGE_SIZE, False, '1 of 3', True)

    def testPostWithFalsePromote(self):
        name = 'base'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithTruePromote(self):
        name = 'base'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostForOneUserAndFalsePromote(self):
        name = 'one'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostForOneUserAndTruePromote(self):
        name = 'one'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostForTwoUsersAndFalsePromote(self):
        name = 'two'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostForTwoUsersAndTruePromote(self):
        name = 'two'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithoutFirstLastAndFalsePromote(self):
        name = 'noal'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithoutFirstLastAndTruePromote(self):
        name = 'noal'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', ''),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithoutSecondLastAndFalsePromote(self):
        name = 'nobl'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithoutSecondLastAndTruePromote(self):
        name = 'nobl'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', ''),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithoutThirdLastAndFalsePromote(self):
        name = 'nocl'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', ''),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithoutThirdLastAndTruePromote(self):
        name = 'nocl'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', ''),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithSpaceAndFalsePromote(self):
        name = 'space'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithSpaceAndTruePromote(self):
        name = 'space'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'al'),
            ('bu', 'bu@d.com', 'bf', 'bl'),
            ('cu', 'cu@d.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithExtraAndFalsePromote(self):
        name = 'extra'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'am al'),
            ('bu', 'bu@d.com', 'bf', 'bm bl'),
            ('cu', 'cu@d.com', 'cf', 'cm cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithExtraAndTruePromote(self):
        name = 'extra'
        domain = 'd.com'
        expected = [
            ('au', 'au@d.com', 'af', 'am al'),
            ('bu', 'bu@d.com', 'bf', 'bm bl'),
            ('cu', 'cu@d.com', 'cf', 'cm cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainAndFalsePromote(self):
        name = 'email'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainAndTruePromote(self):
        name = 'email'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainForOneUserAndFalsePromote(self):
        name = 'email-one'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainForOneUserAndTruePromote(self):
        name = 'email-one'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainForTwoUsersAndFalsePromote(self):
        name = 'email-two'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainForTwoUsersAndTruePromote(self):
        name = 'email-two'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainAndFirstLastAndFalsePromote(self):
        name = 'email-noal'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainAndFirstLastAndTruePromote(self):
        name = 'email-noal'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', ''),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainAndSecondLastAndFalsePromote(self):
        name = 'email-nobl'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainAndSecondLastAndTruePromote(self):
        name = 'email-nobl'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', ''),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailWithoutDomainAndThirdLastAndFalsePromote(self):
        name = 'email-nocl'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', ''),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailWithoutDomainAndThirdLastAndTruePromote(self):
        name = 'email-nocl'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', ''),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailAndSpaceWithoutDomainAndFalsePromote(self):
        name = 'email-space'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailAndSpaceWithoutDomainAndTruePromote(self):
        name = 'email-space'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'al'),
            ('bu', 'be@be.com', 'bf', 'bl'),
            ('cu', 'ce@ce.com', 'cf', 'cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostWithEmailAndExtraWithoutDomainAndFalsePromote(self):
        name = 'email-extra'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'am al'),
            ('bu', 'be@be.com', 'bf', 'bm bl'),
            ('cu', 'ce@ce.com', 'cf', 'cm cl'),
        ]
        self.assertPost(name, domain, False, expected)

    def testPostWithEmailAndExtraWithoutDomainAndTruePromote(self):
        name = 'email-extra'
        domain = None
        expected = [
            ('au', 'ae@ae.com', 'af', 'am al'),
            ('bu', 'be@be.com', 'bf', 'bm bl'),
            ('cu', 'ce@ce.com', 'cf', 'cm cl'),
        ]
        self.assertPost(name, domain, True, expected)

    def testPostEdit(self):
        self.user.email = self.email
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        self.user.save()

        self.user.refresh_from_db()

        self.assertEqual(self.email, self.user.email)
        self.assertEqual(self.first_name, self.user.first_name)
        self.assertEqual(self.last_name, self.user.last_name)
        self.assertNotPower()

        self.superLogin()
        data = {
            'file': BytesIO(' '.join([
                self.username,
                self.other_email,
                self.other_first_name,
                self.other_last_name,
            ]).encode('utf-8')),
            'promote': True,
        }
        self.post(data=data)

        self.user.refresh_from_db()

        self.assertEqual(self.other_email, self.user.email)
        self.assertEqual(self.other_first_name, self.user.first_name)
        self.assertEqual(self.other_last_name, self.user.last_name)
        self.assertPower()


class UserAddViewTests(UserViewTests, ViewTestCase):
    view_name = 'user_add'

    def testPost(self):
        self.superLogin()
        data = {
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        }
        self.post(data=data)
        self.assertTrue(User.objects.filter(**data).exists())


class SingleUserViewTests(UserViewTests):
    def kwargs(self):
        return {'pk': self.user.pk}

    def testGet(self):
        self.superLogin()
        html = self.get_html(kwargs=self.kwargs())
        h2 = html.select_one('h2')
        self.assertIn(self.username, self.string(h2))

    def singlePost(self, data=None):
        self.superLogin()
        self.post(kwargs=self.kwargs(), data=data)


class UserEditViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_edit'

    def testPost(self):
        self.user.email = self.email
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        self.user.save()

        self.user.refresh_from_db()

        self.assertEqual(self.username, self.user.get_username())
        self.assertEqual(self.email, self.user.email)
        self.assertEqual(self.first_name, self.user.first_name)
        self.assertEqual(self.last_name, self.user.last_name)

        self.singlePost({
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        })

        self.user.refresh_from_db()

        self.assertEqual(self.other_username, self.user.get_username())
        self.assertEqual(self.other_email, self.user.email)
        self.assertEqual(self.other_first_name, self.user.first_name)
        self.assertEqual(self.other_last_name, self.user.last_name)


class UserRemoveViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_remove'

    def exists(self):
        return User.objects.filter(pk=self.user.pk).exists()

    def testPost(self):
        self.assertTrue(self.exists())
        self.singlePost()
        self.assertFalse(self.exists())


class UserPromoteViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_promote'

    def testPost(self):
        self.assertNotPower()
        self.singlePost()
        self.assertPower()

    def testIdempotence(self):
        self.singlePost()
        self.singlePost()
        self.assertPower()


class UserDemoteViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_demote'

    def setUp(self):
        super().setUp()
        PowerUser.objects.create(user=self.user)

    def testPost(self):
        self.assertPower()
        self.singlePost()
        self.assertNotPower()

    def testIdempotence(self):
        self.singlePost()
        self.singlePost()
        self.assertNotPower()


class UploadViewTests:
    super_username = 'sus'
    username = 'us'
    power_username = 'pus'

    super_password = 'sp'
    password = 'p'
    power_password = 'pp'

    parent_name = 'pn'
    name = 'n'
    empty_name = ''
    white_name = ' \t\n'
    upper_name = (Asset.name.field.max_length + 1) * 'n'

    uid = 'ui'

    key = 'k'
    empty_key = ''
    white_key = ' \t\n'

    content = b'c'

    redirect_url = 'http://ur'

    csrf_value = 'v'

    def setUp(self):
        User.objects.create_superuser(self.super_username, password=self.super_password)
        User.objects.create_user(self.username, password=self.password)
        self.user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=self.user)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def open(self, content):
        return BytesIO(content)

    def testGetRedirects(self):
        self.assertEqual(302, self.get_status())

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status())

    def testGetForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.get_status())

    def testPostRedirects(self):
        self.assertEqual(302, self.post_status())

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.post_status())

    def testPostForbidsSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.post_status())

    def assertGetStatus(self, query, expected):
        self.powerLogin()
        self.assertEqual(expected, self.get_status(query=query))

    def assertPostStatus(self, data, expected):
        self.powerLogin()
        self.assertEqual(expected, self.post_status(data=data))


class UploadManageViewTests(UploadViewTests, ViewTestCase):
    view_name = 'upload_manage'

    def assertPostsAsset(self, data, expected, exists, parent):
        data['method'] = 'asset'
        data[CSRF_KEY] = self.csrf_value
        self.assertPostStatus(data, expected)
        self.assertEqual(exists, FileAsset.objects.filter(user=self.user, parent=parent, name=self.name).exists())

    def testPostsCode(self):
        data = {
            'method': 'code',
            'name': 'mock',
        }
        self.assertPostStatus(data, 200)

    def testRejectsWithoutMethod(self):
        data = {
            'mock': 'code',
            'name': 'mock',
        }
        self.assertPostStatus(data, 400)

    def testRejectsWithoutName(self):
        data = {
            'method': 'code',
            'mock': 'name',
        }
        self.assertPostStatus(data, 400)

    def testMissesWithWrongMethod(self):
        data = {
            'method': 'mock',
            'name': 'mock',
        }
        self.assertPostStatus(data, 404)

    def testPostsAsset(self):
        data = {
            'name': self.name,
            'path': '',
        }
        self.assertPostsAsset(data, 200, True, None)

    def testPostsAssetWithParent(self):
        parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.parent_name)
        data = {
            'name': self.name,
            'path': self.parent_name,
        }
        self.assertPostsAsset(data, 200, True, parent)

    def testRejectsAssetWithEmptyName(self):
        data = {
            'name': self.empty_name,
            'path': '',
        }
        self.assertPostsAsset(data, 400, False, None)

    def testRejectsAssetWithWhiteName(self):
        data = {
            'name': self.white_name,
            'path': '',
        }
        self.assertPostsAsset(data, 400, False, None)

    def testRejectsAssetWithUpperName(self):
        data = {
            'name': self.upper_name,
            'path': '',
        }
        self.assertPostsAsset(data, 400, False, None)

    def testRejectsAssetWithoutPath(self):
        data = {
            'name': self.name,
            'mock': '',
        }
        self.assertPostsAsset(data, 400, False, None)

    def testMissesAssetWithWrongPath(self):
        data = {
            'name': self.name,
            'path': 'mock',
        }
        self.assertPostsAsset(data, 404, False, None)


class UploadAssetViewTests(UploadViewTests, ViewTestCase):
    view_name = 'upload_asset'

    def assertPostStatusAndData(self, data, expected, exists):
        if settings.CONTAINED:
            self.assertPostStatus(data, 404)
        else:
            self.assertPostStatus(data, expected)
            self.assertEqual(exists, public_storage.exists(self.key))

    def testPostRedirectsAndSaves(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 302, True)

    def testPostRejectsAndDoesNotSaveWithoutKey(self):
        data = {
            'mock': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveWithEmptyKey(self):
        data = {
            'key': self.empty_key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveWithWhiteKey(self):
        data = {
            'key': self.white_key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveWithoutRedirectURL(self):
        data = {
            'key': self.key,
            'mock': self.redirect_url,
            'file': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveWithoutFile(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveWithTwoFiles(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(self.content),
            'mock': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)

    def testPostRejectsAndDoesNotSaveIfInputNotFile(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'mock': self.open(self.content),
        }
        self.assertPostStatusAndData(data, 400, False)


class UploadAssetConfirmViewTests(UploadViewTests, ViewTestCase):
    view_name = 'upload_asset_confirm'

    def assertGetStatusAndData(self, parent, exists, query, expected, active):
        asset = FileAsset.objects.create(user=self.user, parent=parent, name=self.name, uid=self.uid)
        if exists:
            public_storage.save(asset.key(), self.open(self.content))
        self.assertGetStatus(query, expected)
        asset.refresh_from_db()
        self.assertEqual(active, asset.active)

    def testGetRedirectsAndActivates(self):
        query = {
            'key': self.uid,
        }
        self.assertGetStatusAndData(None, True, query, 302, True)

    def testGetRedirectsAndActivatesWithParent(self):
        parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.parent_name)
        query = {
            'key': self.uid,
        }
        self.assertGetStatusAndData(parent, True, query, 302, True)

    def testGetRejectsAndDoesNotActivateWithoutKey(self):
        query = {
            'mock': self.uid,
        }
        self.assertGetStatusAndData(None, True, query, 400, False)

    def testGetRejectsAndDoesNotActivateWithWrongKey(self):
        query = {
            'key': 'mock',
        }
        self.assertGetStatusAndData(None, True, query, 400, False)

    def testGetRedirectsButDoesNotActivateWithoutData(self):
        query = {
            'key': self.uid,
        }
        self.assertGetStatusAndData(None, False, query, 302, False)


class AssetViewTests:
    super_username = 'su'
    username = 'u'
    power_username = 'pu'

    super_password = 'sp'
    password = 'p'
    power_password = 'pp'

    parent_name = '35fde5760c42b7bc'
    name = '528070b65f32f4f7'
    other_name = 'bba8253c7b9a27d2'

    def setUp(self):
        User.objects.create_superuser(self.super_username, password=self.super_password)
        User.objects.create_user(self.username, password=self.password)
        self.user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=self.user)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def kwargs(self):
        return None

    def testGetRedirects(self):
        self.assertEqual(302, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testPostRedirects(self):
        self.assertEqual(302, self.post_status(kwargs=self.kwargs()))

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.post_status(kwargs=self.kwargs()))

    def testPostForbidsSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.post_status(kwargs=self.kwargs()))


class AssetManageViewTests(AssetViewTests, ViewTestCase):
    view_name = 'asset_manage'
    parent = None

    def assertGet(self, num_folders, num_files):
        for i in range(num_folders):
            FolderAsset.objects.create(user=self.user, parent=self.parent, name='{}{}'.format(self.name, i))
        for i in range(num_files):
            FileAsset.objects.create(user=self.user, parent=self.parent, name='{}{}'.format(self.other_name, i))
        self.powerLogin()
        html = self.get_html(kwargs=self.kwargs())
        tables = html.select('table')
        if num_folders:
            folder_trs = tables[0].select('tbody tr')
            if num_files:
                self.assertEqual(2, len(tables))
                file_trs = tables[1].select('tbody tr')
            else:
                self.assertEqual(1, len(tables))
                file_trs = []
        else:
            folder_trs = []
            if num_files:
                self.assertEqual(1, len(tables))
                file_trs = tables[0].select('tbody tr')
            else:
                self.assertEqual(0, len(tables))
                file_trs = []
        self.assertEqual(num_folders, len(folder_trs))
        self.assertEqual(num_files, len(file_trs))

    def testGetForZeroFoldersAndZeroFiles(self):
        self.assertGet(0, 0)

    def testGetForZeroFoldersAndOneFile(self):
        self.assertGet(0, 1)

    def testGetForZeroFoldersAndTwoFiles(self):
        self.assertGet(0, 2)

    def testGetForZeroFoldersAndThreeFiles(self):
        self.assertGet(0, 3)

    def testGetForOneFolderAndZeroFiles(self):
        self.assertGet(1, 0)

    def testGetForOneFolderAndOneFile(self):
        self.assertGet(1, 1)

    def testGetForOneFolderAndTwoFiles(self):
        self.assertGet(1, 2)

    def testGetForOneFolderAndThreeFiles(self):
        self.assertGet(1, 3)

    def testGetForTwoFoldersAndZeroFiles(self):
        self.assertGet(2, 0)

    def testGetForTwoFoldersAndOneFile(self):
        self.assertGet(2, 1)

    def testGetForTwoFoldersAndTwoFiles(self):
        self.assertGet(2, 2)

    def testGetForTwoFoldersAndThreeFiles(self):
        self.assertGet(2, 3)

    def testGetForThreeFoldersAndZeroFiles(self):
        self.assertGet(3, 0)

    def testGetForThreeFoldersAndOneFile(self):
        self.assertGet(3, 1)

    def testGetForThreeFoldersAndTwoFiles(self):
        self.assertGet(3, 2)

    def testGetForThreeFoldersAndThreeFiles(self):
        self.assertGet(3, 3)


class AssetWithParentTests:
    def setUp(self):
        super().setUp()
        self.parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.parent_name)


class AssetFolderViewTests(AssetWithParentTests, AssetManageViewTests):
    view_name = 'asset_folder'

    def kwargs(self):
        return {'path': self.parent.name}


class SingleAssetViewTests(AssetWithParentTests, AssetViewTests):
    Asset = FolderAsset

    def setUp(self):
        super().setUp()
        self.child = self.Asset.objects.create(user=self.user, parent=self.parent, name=self.name)

    def kwargs(self):
        return {'path': '{}/{}'.format(self.parent.name, self.name)}

    def testGet(self):
        self.powerLogin()
        html = self.get_html(kwargs=self.kwargs())
        h2 = html.select_one('h2')
        self.assertIn(self.name, self.string(h2))

    def singlePost(self, data=None):
        self.powerLogin()
        self.post(kwargs=self.kwargs(), data=data)


class AssetEditViewTests(SingleAssetViewTests, ViewTestCase):
    view_name = 'asset_edit'

    def testPost(self):
        self.assertEqual(self.name, self.child.name)
        self.singlePost({
            'name': self.other_name,
        })
        self.child.refresh_from_db()
        self.assertEqual(self.other_name, self.child.name)


class AssetEditFileViewTests(SingleAssetViewTests, ViewTestCase):
    view_name = 'asset_edit_file'
    Asset = FileAsset


class AssetRemoveViewTests(SingleAssetViewTests, ViewTestCase):
    view_name = 'asset_remove'

    def exists(self):
        return self.Asset.objects.filter(user=self.user, parent=self.parent, name=self.name).exists()

    def testPost(self):
        self.assertTrue(self.exists())
        self.singlePost()
        self.assertFalse(self.exists())


class AssetRemoveFileViewTests(SingleAssetViewTests, ViewTestCase):
    view_name = 'asset_remove_file'
    Asset = FileAsset
