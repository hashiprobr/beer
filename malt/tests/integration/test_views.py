import os

from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model

from beer import public_storage
from beer.tests import ViewTestCase

from ...models import PowerUser, FolderAsset, FileAsset
from ...caches import power_cache
from ...views import PAGE_SIZE

User = get_user_model()


class UserViewTests:
    username = '1af81dab46c4d2c8'
    power_username = '35fde5760c42b7bc'
    super_username = '528070b65f32f4f7'
    other_username = 'bba8253c7b9a27d2'

    usernames = [
        'aaadddeee',
        'aaaeeeddd',
        'fffbbbggg',
        'gggbbbfff',
        'hhhiiiccc',
        'iiihhhccc',
    ]

    password = 'p'
    power_password = 'pp'
    super_password = 'sp'

    email = 'e@e.com'
    other_email = 'oe@oe.com'

    first_name = 'f'
    other_first_name = 'of'

    last_name = 'l'
    other_last_name = 'ol'

    def setUp(self):
        self.user = User.objects.create_user(self.username, password=self.password, email=self.email, first_name=self.first_name, last_name=self.last_name)
        power_user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=power_user)
        User.objects.create_superuser(self.super_username, password=self.super_password)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def power(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def kwargs(self):
        return None

    def assertExists(self, username, email, first_name, last_name):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail('User.DoesNotExist raised')
        self.assertEqual(email, user.email)
        self.assertEqual(first_name, user.first_name)
        self.assertEqual(last_name, user.last_name)
        return user

    def assertDoesNotExist(self, username):
        self.assertFalse(User.objects.filter(username=username).exists())

    def assertPower(self, user):
        self.assertTrue(self.power(user))
        self.assertTrue(power_cache.get(user))

    def assertNotPower(self, user):
        self.assertFalse(self.power(user))
        self.assertFalse(power_cache.get(user))

    def assertBlocks(self, response):
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.get('Location').startswith('/login'))

    def testGetBlocks(self):
        response = self.get(kwargs=self.kwargs())
        self.assertBlocks(response)

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterPowerLogin(self):
        self.powerLogin()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testGetAcceptsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(200, self.get_status(kwargs=self.kwargs()))


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

    def create(self, users):
        for username, email, first_name, last_name, actual in users:
            user = User.objects.create(username=username, email=email, first_name=first_name, last_name=last_name)
            if actual:
                PowerUser.objects.create(user=user)

    def post(self, name, promote):
        data = {
            'file': self.open(name),
            'domain': 'd.com',
            'promote': promote,
        }
        return super().post(kwargs=self.kwargs(), data=data)

    def assertGetsFilter(self, filter, expected):
        for username in self.usernames:
            User.objects.create_user(username)
        self.superLogin()
        if filter is None:
            query = None
        else:
            query = {'filter': filter}
        html = self.get_html(kwargs=self.kwargs(), query=query)
        trs = html.select('tbody tr')
        actual = [self.string(tr.select_one('td')) for tr in trs]
        self.assertEqual(expected, actual)

    def assertGetsPage(self, n, page, length, left, center, right):
        for i in range(n - 3):
            User.objects.create_user(str(i))
        self.superLogin()
        if page is None:
            query = None
        else:
            query = {'page': page}
        html = self.get_html(kwargs=self.kwargs(), query=query)
        trs = html.select('tbody tr')
        caption = html.select_one('caption')
        arrows = [self.string(a) for a in caption.select('a')]
        self.assertEqual(length, len(trs))
        self.assertEqual(left, '🡨' in arrows)
        self.assertIn(center, self.string(caption))
        self.assertEqual(right, '🡪' in arrows)

    def assertPosts(self, name, promote, users):
        self.superLogin()
        response = self.post(name, promote)
        self.assertEqual(302, response.status_code)
        for username, email, first_name, last_name, expected in users:
            user = self.assertExists(username, email, first_name, last_name)
            if expected:
                self.assertPower(user)
            else:
                self.assertNotPower(user)

    def testGetsWithoutFilter(self):
        self.assertGetsFilter(None, [
            self.username,
            self.power_username,
            self.super_username,
            *self.usernames,
        ])

    def testGetsWithPrefixFilter(self):
        self.assertGetsFilter('aaa', [
            'aaadddeee',
            'aaaeeeddd',
        ])

    def testGetsWithMiddleFilter(self):
        self.assertGetsFilter('bbb', [
            'fffbbbggg',
            'gggbbbfff',
        ])

    def testGetsWithSuffixFilter(self):
        self.assertGetsFilter('ccc', [
            'hhhiiiccc',
            'iiihhhccc',
        ])

    def testGetsWithBadFilter(self):
        self.assertGetsFilter('ooo', [
        ])

    def testPageSize(self):
        self.assertGreaterEqual(PAGE_SIZE, 6)

    def testGetsForHalfPageWithoutPage(self):
        self.assertGetsPage(PAGE_SIZE // 2, None, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetsForHalfPageWithPageZero(self):
        self.assertGetsPage(PAGE_SIZE // 2, 0, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetsForHalfPageWithPageOne(self):
        self.assertGetsPage(PAGE_SIZE // 2, 1, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetsForHalfPageWithPageTwo(self):
        self.assertGetsPage(PAGE_SIZE // 2, 2, PAGE_SIZE // 2, False, '1 of 1', False)

    def testGetsForOnePageWithoutPage(self):
        self.assertGetsPage(PAGE_SIZE, None, PAGE_SIZE, False, '1 of 1', False)

    def testGetsForOnePageWithPageZero(self):
        self.assertGetsPage(PAGE_SIZE, 0, PAGE_SIZE, False, '1 of 1', False)

    def testGetsForOnePageWithPageOne(self):
        self.assertGetsPage(PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 1', False)

    def testGetsForOnePageWithPageTwo(self):
        self.assertGetsPage(PAGE_SIZE, 2, PAGE_SIZE, False, '1 of 1', False)

    def testGetsForOneHalfPageWithoutPage(self):
        self.assertGetsPage(3 * PAGE_SIZE // 2, None, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForOneHalfPageWithPageZero(self):
        self.assertGetsPage(3 * PAGE_SIZE // 2, 0, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForOneHalfPageWithPageOne(self):
        self.assertGetsPage(3 * PAGE_SIZE // 2, 1, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForOneHalfPageWithPageTwo(self):
        self.assertGetsPage(3 * PAGE_SIZE // 2, 2, PAGE_SIZE // 2, True, '2 of 2', False)

    def testGetsForOneHalfPageWithPageThree(self):
        self.assertGetsPage(3 * PAGE_SIZE // 2, 3, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForTwoPagesWithoutPage(self):
        self.assertGetsPage(2 * PAGE_SIZE, None, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForTwoPagesWithPageZero(self):
        self.assertGetsPage(2 * PAGE_SIZE, 0, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForTwoPagesWithPageOne(self):
        self.assertGetsPage(2 * PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForTwoPagesWithPageTwo(self):
        self.assertGetsPage(2 * PAGE_SIZE, 2, PAGE_SIZE, True, '2 of 2', False)

    def testGetsForTwoPagesWithPageThree(self):
        self.assertGetsPage(2 * PAGE_SIZE, 3, PAGE_SIZE, False, '1 of 2', True)

    def testGetsForTwoHalfPagesWithoutPage(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, None, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForTwoHalfPagesWithPageZero(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, 0, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForTwoHalfPagesWithPageOne(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, 1, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForTwoHalfPagesWithPageTwo(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, 2, PAGE_SIZE, True, '2 of 3', True)

    def testGetsForTwoHalfPagesWithPageThree(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, 3, PAGE_SIZE // 2, True, '3 of 3', False)

    def testGetsForTwoHalfPagesWithPageFour(self):
        self.assertGetsPage(5 * PAGE_SIZE // 2, 4, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForThreePagesWithoutPage(self):
        self.assertGetsPage(3 * PAGE_SIZE, None, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForThreePagesWithPageZero(self):
        self.assertGetsPage(3 * PAGE_SIZE, 0, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForThreePagesWithPageOne(self):
        self.assertGetsPage(3 * PAGE_SIZE, 1, PAGE_SIZE, False, '1 of 3', True)

    def testGetsForThreePagesWithPageTwo(self):
        self.assertGetsPage(3 * PAGE_SIZE, 2, PAGE_SIZE, True, '2 of 3', True)

    def testGetsForThreePagesWithPageThree(self):
        self.assertGetsPage(3 * PAGE_SIZE, 3, PAGE_SIZE, True, '3 of 3', False)

    def testGetsForThreePagesWithPageFour(self):
        self.assertGetsPage(3 * PAGE_SIZE, 4, PAGE_SIZE, False, '1 of 3', True)

    def testDoesNotExist(self):
        self.assertDoesNotExist('au')
        self.assertDoesNotExist('bu')

    def testPostBlocks(self):
        response = self.post('one', False)
        self.assertBlocks(response)

    def testPostForbidsAfterLogin(self):
        self.login()
        response = self.post('one', False)
        self.assertEqual(403, response.status_code)

    def testPostForbidsAfterPowerLogin(self):
        self.powerLogin()
        response = self.post('one', False)
        self.assertEqual(403, response.status_code)

    def testPostsOneWithFalse(self):
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
        ])

    def testPostsOneWithTrue(self):
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
        ])

    def testPostsTwoWithFalse(self):
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testPostsTwoWithTrue(self):
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasFirstWithFalsePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
        ])

    def testHasFirstWithFalsePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
        ])

    def testHasFirstWithFalsePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasFirstWithFalsePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasFirstWithTruePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
        ])

    def testHasFirstWithTruePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
        ])

    def testHasFirstWithTruePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasFirstWithTruePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasSecondWithFalsePostsOneWithFalse(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])

    def testHasSecondWithFalsePostsOneWithTrue(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])

    def testHasSecondWithFalsePostsTwoWithFalse(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasSecondWithFalsePostsTwoWithTrue(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasSecondWithTruePostsOneWithFalse(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasSecondWithTruePostsOneWithTrue(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasSecondWithTruePostsTwoWithFalse(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasSecondWithTruePostsTwoWithTrue(self):
        self.create([
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasTwoWithFalseFalsePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
        ])

    def testHasTwoWithFalseFalsePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
        ])

    def testHasTwoWithFalseFalsePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasTwoWithFalseFalsePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasTwoWithFalseTruePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasTwoWithFalseTruePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasTwoWithFalseTruePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasTwoWithFalseTruePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasTwoWithTrueFalsePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])

    def testHasTwoWithTrueFalsePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])

    def testHasTwoWithTrueFalsePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasTwoWithTrueFalsePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', False),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])

    def testHasTwoWithTrueTruePostsOneWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasTwoWithTrueTruePostsOneWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('one', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])

    def testHasTwoWithTrueTruePostsTwoWithFalse(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', False, [
            ('au', 'au@d.com', 'af', 'al', False),
            ('bu', 'bu@d.com', 'bf', 'bl', False),
        ])

    def testHasTwoWithTrueTruePostsTwoWithTrue(self):
        self.create([
            ('au', 'ae@ae.com', 'oaf', 'oal', True),
            ('bu', 'be@be.com', 'obf', 'obl', True),
        ])
        self.assertPosts('two', True, [
            ('au', 'au@d.com', 'af', 'al', True),
            ('bu', 'bu@d.com', 'bf', 'bl', True),
        ])


class SingleUserViewTests(UserViewTests):
    def data(self):
        return None

    def post(self):
        return super().post(kwargs=self.kwargs(), data=self.data())

    def assertPosts(self):
        self.superLogin()
        response = self.post()
        self.assertEqual(302, response.status_code)

    def testPostBlocks(self):
        response = self.post()
        self.assertBlocks(response)

    def testPostForbidsAfterLogin(self):
        self.login()
        response = self.post()
        self.assertEqual(403, response.status_code)

    def testPostForbidsAfterPowerLogin(self):
        self.powerLogin()
        response = self.post()
        self.assertEqual(403, response.status_code)


class UserAddViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_add'

    def data(self):
        return {
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        }

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.other_username)

    def testPosts(self):
        self.assertPosts()
        self.assertExists(self.other_username, self.other_email, self.other_first_name, self.other_last_name)


class SpecificUserViewTests(SingleUserViewTests):
    def kwargs(self):
        return {'pk': self.user.pk}

    def testGets(self):
        self.superLogin()
        html = self.get_html(kwargs=self.kwargs())
        h2 = html.select_one('h2')
        self.assertIn(self.user.get_username(), self.string(h2))


class UserEditViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_edit'

    def data(self):
        return {
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        }

    def testDoesNotExist(self):
        self.assertEqual(self.username, self.user.get_username())
        self.assertEqual(self.email, self.user.email)
        self.assertEqual(self.first_name, self.user.first_name)
        self.assertEqual(self.last_name, self.user.last_name)

    def testPosts(self):
        self.assertPosts()
        self.user.refresh_from_db()
        self.assertEqual(self.other_username, self.user.get_username())
        self.assertEqual(self.other_email, self.user.email)
        self.assertEqual(self.other_first_name, self.user.first_name)
        self.assertEqual(self.other_last_name, self.user.last_name)


class UserRemoveViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_remove'

    def testExists(self):
        self.assertExists(self.username, self.email, self.first_name, self.last_name)

    def testPosts(self):
        self.assertPosts()
        self.assertDoesNotExist(self.username)


class UserPromoteViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_promote'

    def testDoesNotExist(self):
        self.assertNotPower(self.user)

    def testPosts(self):
        self.assertPosts()
        self.assertPower(self.user)

    def testPostsPosts(self):
        self.assertPosts()
        self.assertPosts()
        self.assertPower(self.user)


class UserDemoteViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_demote'

    def setUp(self):
        super().setUp()
        PowerUser.objects.create(user=self.user)

    def testExists(self):
        self.assertPower(self.user)

    def testPosts(self):
        self.assertPosts()
        self.assertNotPower(self.user)

    def testPostsPosts(self):
        self.assertPosts()
        self.assertPosts()
        self.assertNotPower(self.user)


class UploadViewTests:
    username = 'us'
    super_username = 'sus'
    power_username = 'pus'

    password = 'p'
    super_password = 'sp'
    power_password = 'pp'

    grand_parent_name = 'gpn'
    parent_name = 'pn'
    name = 'n'
    empty_name = ''
    white_name = ' \t\n'
    slash_name = 'n/n'

    key = 'k'
    empty_key = ''
    white_key = ' \t\n'

    redirect_url = 'http://ur'

    uid = 'ui'

    def setUp(self):
        User.objects.create_user(self.username, password=self.password)
        User.objects.create_superuser(self.super_username, password=self.super_password)
        self.user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=self.user)

        self.upper_name = (FileAsset.name.field.max_length + 1) * 'n'

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.grand_parent_name)
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=self.parent_name)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def open(self):
        return BytesIO(b'c')

    def assertBlocks(self, response):
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.get('Location').startswith('/login'))


class PostUploadViewTests(UploadViewTests):
    def assertPostBlocks(self, data):
        response = self.post(data=data)
        self.assertBlocks(response)

    def assertPostForbidsAfterLogin(self, data):
        self.login()
        self.assertEqual(403, self.post_status(data=data))

    def assertPostForbidsAfterSuperLogin(self, data):
        self.superLogin()
        self.assertEqual(403, self.post_status(data=data))

    def assertPosts(self, data, expected):
        self.powerLogin()
        self.assertEqual(expected, self.post_status(data=data))

    def testGetBlocks(self):
        response = self.get()
        self.assertBlocks(response)

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status())

    def testGetForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.get_status())

    def testGetDisallowsAfterPowerLogin(self):
        self.powerLogin()
        self.assertEqual(405, self.get_status())


class UploadManageViewTests(PostUploadViewTests, ViewTestCase):
    view_name = 'upload_manage'

    def exists(self, parent):
        return FileAsset.objects.filter(user=self.user, parent=parent, name=self.name).exists()

    def update(self, data):
        data['method'] = 'asset'
        try:
            data['path'] = '/'.join(data['path'])
        except KeyError:
            pass

    def assertPostsAsset(self, data, parent):
        self.update(data)
        self.assertPosts(data, 200)
        self.assertTrue(self.exists(parent))

    def assertDoesNotPostAsset(self, data, expected):
        self.update(data)
        self.assertPosts(data, expected)

    def testPostBlocks(self):
        data = {
            'method': 'code',
            'name': self.name,
        }
        self.assertPostBlocks(data)

    def testPostForbidsAfterLogin(self):
        data = {
            'method': 'code',
            'name': self.name,
        }
        self.assertPostForbidsAfterLogin(data)

    def testPostForbidsAfterSuperLogin(self):
        data = {
            'method': 'code',
            'name': self.name,
        }
        self.assertPostForbidsAfterSuperLogin(data)

    def testPostRejectsWithoutMethod(self):
        data = {
            'mock': 'code',
            'name': self.name,
        }
        self.assertPosts(data, 400)

    def testPostRejectsWithoutName(self):
        data = {
            'method': 'code',
            'mock': self.name,
        }
        self.assertPosts(data, 400)

    def testPostMissesWithWrongMethod(self):
        data = {
            'method': 'mock',
            'name': self.name,
        }
        self.assertPosts(data, 404)

    def testPostsCode(self):
        data = {
            'method': 'code',
            'name': self.name,
        }
        self.assertPosts(data, 200)

    def testDoesNotExist(self):
        self.assertFalse(self.exists(None))
        self.assertFalse(self.exists(self.grand_parent))
        self.assertFalse(self.exists(self.parent))

    def testPostsAsset(self):
        data = {
            'name': self.name,
            'path': [self.grand_parent_name, self.parent_name],
        }
        self.assertPostsAsset(data, self.parent)

    def testPostRejectsAssetWithEmptyName(self):
        data = {
            'name': self.empty_name,
            'path': [self.grand_parent_name, self.parent_name],
        }
        self.assertDoesNotPostAsset(data, 400)

    def testPostRejectsAssetWithWhiteName(self):
        data = {
            'name': self.white_name,
            'path': [self.grand_parent_name, self.parent_name],
        }
        self.assertDoesNotPostAsset(data, 400)

    def testPostRejectsAssetWithSlashName(self):
        data = {
            'name': self.slash_name,
            'path': [self.grand_parent_name, self.parent_name],
        }
        self.assertDoesNotPostAsset(data, 400)

    def testPostRejectsAssetWithUpperName(self):
        data = {
            'name': self.upper_name,
            'path': [self.grand_parent_name, self.parent_name],
        }
        self.assertDoesNotPostAsset(data, 400)

    def testPostRejectsAssetWithoutPath(self):
        data = {
            'name': self.name,
            'mock': [self.grand_parent_name, self.parent_name],
        }
        self.assertDoesNotPostAsset(data, 400)

    def testPostMissesAssetWithWrongPath(self):
        data = {
            'name': self.name,
            'path': ['mock'],
        }
        self.assertDoesNotPostAsset(data, 404)

    def testPostsAssetWithNoneParent(self):
        data = {
            'name': self.name,
            'path': [],
        }
        self.assertPostsAsset(data, None)

    def testPostsAssetWithGrandParent(self):
        data = {
            'name': self.name,
            'path': [self.grand_parent_name],
        }
        self.assertPostsAsset(data, self.grand_parent)


class UploadCodeViewTests(PostUploadViewTests, ViewTestCase):
    view_name = 'upload_code'

    def testPostBlocks(self):
        self.assertPostBlocks(None)

    def testPostForbidsAfterLogin(self):
        self.assertPostForbidsAfterLogin(None)

    def testPostForbidsAfterSuperLogin(self):
        self.assertPostForbidsAfterSuperLogin(None)

    def testPosts(self):
        self.assertPosts(None, 200)


class UploadAssetViewTests(PostUploadViewTests, ViewTestCase):
    view_name = 'upload_asset'

    def exists(self):
        return public_storage.exists(self.key)

    def assertPostsLocal(self, data):
        if settings.CONTAINED:
            self.assertPosts(data, 404)
        else:
            self.assertPosts(data, 302)
            self.assertTrue(self.exists())

    def assertDoesNotPostLocal(self, data, expected):
        if settings.CONTAINED:
            self.assertPosts(data, 404)
        else:
            self.assertPosts(data, expected)

    def testDoesNotExist(self):
        self.assertFalse(self.exists())

    def testPostBlocks(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertPostBlocks(data)

    def testPostForbidsAfterLogin(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertPostForbidsAfterLogin(data)

    def testPostForbidsAfterSuperLogin(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertPostForbidsAfterSuperLogin(data)

    def testPosts(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertPostsLocal(data)

    def testPostRejectsWithoutKey(self):
        data = {
            'mock': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithEmptyKey(self):
        data = {
            'key': self.empty_key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithWhiteKey(self):
        data = {
            'key': self.white_key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithoutRedirectURL(self):
        data = {
            'key': self.key,
            'mock': self.redirect_url,
            'file': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithWrongRedirectURL(self):
        data = {
            'key': self.key,
            'success_action_redirect': 'mock',
            'file': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithoutFile(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsWithTwoFiles(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.open(),
            'mock': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)

    def testPostRejectsIfInputNotFile(self):
        data = {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'mock': self.open(),
        }
        self.assertDoesNotPostLocal(data, 400)


class UploadAssetConfirmViewTests(UploadViewTests, ViewTestCase):
    view_name = 'upload_asset_confirm'

    def exists(self, parent):
        return FileAsset.objects.filter(user=self.user, parent=parent, name=self.name).exists()

    def create(self, parent):
        file_asset = FileAsset.objects.create(user=self.user, parent=parent, name=self.name)
        file_asset.uid = self.uid
        file_asset.save()
        return file_asset

    def assertGets(self, query, parent):
        self.powerLogin()
        self.assertEqual(302, self.get_status(query=query))
        self.assertTrue(self.exists(parent))

    def assertDoesNotGet(self, query, expected):
        self.powerLogin()
        self.assertEqual(expected, self.get_status(query=query))

    def testDoesNotExist(self):
        file_asset = self.create(self.parent)
        self.assertFalse(file_asset.active)

    def testGetBlocks(self):
        self.create(self.parent)
        query = {
            'key': self.uid,
        }
        response = self.get(query=query)
        self.assertBlocks(response)

    def testGetForbidsAfterLogin(self):
        self.create(self.parent)
        query = {
            'key': self.uid,
        }
        self.login()
        self.assertEqual(403, self.get_status(query=query))

    def testGetForbidsAfterSuperLogin(self):
        self.create(self.parent)
        query = {
            'key': self.uid,
        }
        self.superLogin()
        self.assertEqual(403, self.get_status(query=query))

    def testGetsWithFile(self):
        file_asset = self.create(self.parent)
        key = file_asset.key()
        file = self.open()
        public_storage.save(key, file)
        query = {
            'key': self.uid,
        }
        self.assertGets(query, self.parent)
        file_asset.refresh_from_db()
        self.assertTrue(file_asset.active)

    def testGets(self):
        self.create(self.parent)
        query = {
            'key': self.uid,
        }
        self.assertGets(query, self.parent)

    def testGetsWithNoneParent(self):
        self.create(None)
        query = {
            'key': self.uid,
        }
        self.assertGets(query, None)

    def testGetsWithGrandParent(self):
        self.create(self.grand_parent)
        query = {
            'key': self.uid,
        }
        self.assertGets(query, self.grand_parent)

    def testGetMissesWithoutFileAsset(self):
        query = {
            'key': self.uid,
        }
        self.assertDoesNotGet(query, 404)

    def testGetRejectsWithoutKey(self):
        self.create(self.parent)
        query = {
            'mock': self.uid,
        }
        self.assertDoesNotGet(query, 400)

    def testGetMissesWithWrongKey(self):
        self.create(self.parent)
        query = {
            'key': 'mock',
        }
        self.assertDoesNotGet(query, 404)

    def testPostBlocks(self):
        response = self.post()
        self.assertBlocks(response)

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.post_status())

    def testPostForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.post_status())

    def testPostDisallowsAfterPowerLogin(self):
        self.powerLogin()
        self.assertEqual(405, self.post_status())


class AssetViewTests:
    trashed = False
    Asset = FolderAsset

    username = 'u'
    super_username = 'su'
    power_username = 'pu'

    password = 'p'
    super_password = 'sp'
    power_password = 'pp'

    grand_parent_name = '1cb3bba7d6539fd8'
    other_grand_parent_name = '35fde5760c42b7bc'
    parent_name = '528070b65f32f4f7'
    other_parent_name = '6bdc514167a3db99'
    child_name = '8a8e367c2ebfd83a'
    grand_child_name = '9cb85ee9f59d0296'
    name = 'bba8253c7b9a27d2'
    other_name = 'eceeae86d5766723'

    def setUp(self):
        User.objects.create_user(self.username, password=self.password)
        User.objects.create_superuser(self.super_username, password=self.super_password)
        self.user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=self.user)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def object(self):
        return None

    def names(self):
        return []

    def kwargs(self):
        return None

    def data(self):
        return None

    def post(self):
        return super().post(kwargs=self.kwargs(), data=self.data())

    def exists(self, parent, name, trashed):
        return self.Asset.objects.filter(user=self.user, parent=parent, name=name, trashed=trashed).exists()

    def existsBase(self, trashed):
        return self.exists(self.object(), self.name, trashed)

    def assertSource(self, expected):
        self.assertEqual(expected, self.existsBase(self.trashed))

    def assertBlocks(self, response):
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.get('Location').startswith('/login'))

    def assertPosts(self):
        self.powerLogin()
        response = self.post()
        self.assertEqual(302, response.status_code)

    def testGetBlocks(self):
        response = self.get(kwargs=self.kwargs())
        self.assertBlocks(response)

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertEqual(403, self.get_status(kwargs=self.kwargs()))

    def testPostBlocks(self):
        response = self.post()
        self.assertBlocks(response)

    def testPostForbidsAfterLogin(self):
        self.login()
        response = self.post()
        self.assertEqual(403, response.status_code)

    def testPostForbidsAfterSuperLogin(self):
        self.superLogin()
        response = self.post()
        self.assertEqual(403, response.status_code)


class AssetGetMixin:
    def testGetAcceptsAfterPowerLogin(self):
        self.powerLogin()
        self.assertEqual(200, self.get_status(kwargs=self.kwargs()))


class BrowsingAssetViewTests(AssetGetMixin, AssetViewTests):
    def testGetsForZeroFoldersAndZeroFiles(self):
        self.assertGets(0, 0)

    def testGetsForZeroFoldersAndOneFile(self):
        self.assertGets(0, 1)

    def testGetsForZeroFoldersAndTwoFiles(self):
        self.assertGets(0, 2)

    def testGetsForZeroFoldersAndThreeFiles(self):
        self.assertGets(0, 3)

    def testGetsForOneFolderAndZeroFiles(self):
        self.assertGets(1, 0)

    def testGetsForOneFolderAndOneFile(self):
        self.assertGets(1, 1)

    def testGetsForOneFolderAndTwoFiles(self):
        self.assertGets(1, 2)

    def testGetsForOneFolderAndThreeFiles(self):
        self.assertGets(1, 3)

    def testGetsForTwoFoldersAndZeroFiles(self):
        self.assertGets(2, 0)

    def testGetsForTwoFoldersAndOneFile(self):
        self.assertGets(2, 1)

    def testGetsForTwoFoldersAndTwoFiles(self):
        self.assertGets(2, 2)

    def testGetsForTwoFoldersAndThreeFiles(self):
        self.assertGets(2, 3)

    def testGetsForThreeFoldersAndZeroFiles(self):
        self.assertGets(3, 0)

    def testGetsForThreeFoldersAndOneFile(self):
        self.assertGets(3, 1)

    def testGetsForThreeFoldersAndTwoFiles(self):
        self.assertGets(3, 2)

    def testGetsForThreeFoldersAndThreeFiles(self):
        self.assertGets(3, 3)


class AssetGrandParentMixin:
    def setUp(self):
        super().setUp()
        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.grand_parent_name)


class AssetParentMixin(AssetGrandParentMixin):
    def setUp(self):
        super().setUp()
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=self.parent_name)


class AssetFolderMixin:
    def object(self):
        return self.grand_parent

    def names(self):
        return [self.grand_parent_name]


class AssetSubMixin:
    def object(self):
        return self.parent

    def names(self):
        return [self.grand_parent_name, self.parent_name]


class AssetManageViewTests(BrowsingAssetViewTests, ViewTestCase):
    view_name = 'asset_manage'

    def data(self):
        return {
            'name': self.name,
        }

    def assertGets(self, num_folders, num_files):
        for i in range(num_folders):
            FolderAsset.objects.create(user=self.user, parent=self.object(), name=str(i))
        for i in range(num_files):
            FileAsset.objects.create(user=self.user, parent=self.object(), name=str(i))
        self.powerLogin()
        html = self.get_html(kwargs=self.kwargs())
        tables = html.select('table')
        if num_folders:
            folder_trs = tables[0].select('tbody tr')
            if num_files:
                file_trs = tables[1].select('tbody tr')
            else:
                file_trs = []
        else:
            folder_trs = []
            if num_files:
                file_trs = tables[0].select('tbody tr')
            else:
                file_trs = []
        self.assertEqual(num_folders, len(folder_trs))
        self.assertEqual(num_files, len(file_trs))

    def testDoesNotExist(self):
        self.assertSource(False)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(True)


class AssetFolderManageViewTests(AssetFolderMixin, AssetGrandParentMixin, AssetManageViewTests):
    view_name = 'asset_manage_folder'

    def kwargs(self):
        return {'path': '/'.join(self.names())}


class AssetSubFolderManageViewTests(AssetSubMixin, AssetParentMixin, AssetFolderManageViewTests):
    pass


class SingleAssetViewTests(AssetParentMixin, AssetViewTests):
    def setUp(self):
        super().setUp()
        self.other_grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.other_grand_parent_name)
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=self.other_parent_name)
        self.child = FolderAsset.objects.create(user=self.user, parent=self.parent, name=self.child_name)
        self.grand_child = FolderAsset.objects.create(user=self.user, parent=self.child, name=self.grand_child_name)
        self.asset = self.Asset.objects.create(user=self.user, parent=self.object(), name=self.name)

    def path(self):
        return '/'.join([*self.names(), self.name])


class PathAssetViewTests(SingleAssetViewTests):
    def kwargs(self):
        return {'path': self.path()}


class SpecificAssetMixin(AssetGetMixin):
    def substring(self):
        return self.name

    def testGets(self):
        self.powerLogin()
        html = self.get_html(kwargs=self.kwargs())
        h2 = html.select_one('h2')
        self.assertIn(self.substring(), self.string(h2))


class AssertUpdateMixin:
    def testKeeps(self):
        self.assertSource(True)
        self.assertTarget(False)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(False)
        self.assertTarget(True)


class AssetFileMixin:
    Asset = FileAsset


class AssetMoveViewTests(AssertUpdateMixin, SpecificAssetMixin, PathAssetViewTests):
    view_name = 'asset_move'

    def data(self):
        return {
            'path': '/'.join([*self.targetNames(), self.targetName()]),
        }

    def assertTarget(self, expected):
        self.assertEqual(expected, self.exists(self.targetObject(), self.targetName(), self.trashed))

    def targetName(self):
        return self.name

    def targetObject(self):
        return None

    def targetNames(self):
        return []


class AssetMoveFileMixin(AssetFileMixin):
    view_name = 'asset_move_file'


class AssetMoveNameViewTests(AssetMoveViewTests, ViewTestCase):
    def targetName(self):
        return self.other_name


class AssetMoveNameFileViewTests(AssetMoveFileMixin, AssetMoveNameViewTests):
    pass


class AssetMoveDownOneViewTests(AssetMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.grand_parent

    def targetNames(self):
        return [self.grand_parent_name]


class AssetMoveDownOneFileViewTests(AssetMoveFileMixin, AssetMoveDownOneViewTests):
    pass


class AssetMoveDownTwoViewTests(AssetMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.parent

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetMoveDownTwoViewTests):
    pass


class AssetFolderMoveViewTests(AssetFolderMixin, AssetMoveViewTests):
    pass


class AssetFolderMoveNameViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def targetName(self):
        return self.other_name

    def targetObject(self):
        return self.grand_parent

    def targetNames(self):
        return [self.grand_parent_name]


class AssetFolderMoveNameFileViewTests(AssetMoveFileMixin, AssetFolderMoveNameViewTests):
    pass


class AssetFolderMoveUpViewTests(AssetFolderMoveViewTests, ViewTestCase):
    pass


class AssetFolderMoveUpFileViewTests(AssetMoveFileMixin, AssetFolderMoveUpViewTests):
    pass


class AssetFolderMoveSideViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.other_grand_parent

    def targetNames(self):
        return [self.other_grand_parent_name]


class AssetFolderMoveSideFileViewTests(AssetMoveFileMixin, AssetFolderMoveSideViewTests):
    pass


class AssetFolderMoveDownOneViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.parent

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetFolderMoveDownOneFileViewTests(AssetMoveFileMixin, AssetFolderMoveDownOneViewTests):
    pass


class AssetFolderMoveDownTwoViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.child

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name]


class AssetFolderMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetFolderMoveDownTwoViewTests):
    pass


class AssetSubFolderMoveViewTests(AssetSubMixin, AssetFolderMoveViewTests):
    pass


class AssetSubFolderMoveNameViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def targetName(self):
        return self.other_name

    def targetObject(self):
        return self.parent

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetSubFolderMoveNameFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveNameViewTests):
    pass


class AssetSubFolderMoveUpOneViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.grand_parent

    def targetNames(self):
        return [self.grand_parent_name]


class AssetSubFolderMoveUpOneFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveUpOneViewTests):
    pass


class AssetSubFolderMoveUpTwoViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    pass


class AssetSubFolderMoveUpTwoFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveUpTwoViewTests):
    pass


class AssetSubFolderMoveSideViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.other_parent

    def targetNames(self):
        return [self.grand_parent_name, self.other_parent_name]


class AssetSubFolderMoveSideFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveSideViewTests):
    pass


class AssetSubFolderMoveDownOneViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.child

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name]


class AssetSubFolderMoveDownOneFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveDownOneViewTests):
    pass


class AssetSubFolderMoveDownTwoViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def targetObject(self):
        return self.grand_child

    def targetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name, self.grand_child_name]


class AssetSubFolderMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveDownTwoViewTests):
    pass


class AssetRecycleMixin(AssertUpdateMixin):
    def testGetDisallowsAfterPowerLogin(self):
        self.powerLogin()
        self.assertEqual(405, self.get_status(kwargs=self.kwargs()))

    def assertTarget(self, expected):
        self.assertEqual(expected, self.existsBase(not self.trashed))


class AssetTrashViewTests(AssetRecycleMixin, PathAssetViewTests, ViewTestCase):
    view_name = 'asset_trash'


class AssetFolderTrashViewTests(AssetFolderMixin, AssetTrashViewTests):
    pass


class AssetSubFolderTrashViewTests(AssetSubMixin, AssetFolderTrashViewTests):
    pass


class AssetTrashFileViewTests(AssetFileMixin, AssetTrashViewTests):
    view_name = 'asset_trash_file'


class AssetFolderTrashFileViewTests(AssetFolderMixin, AssetTrashFileViewTests):
    pass


class AssetSubFolderTrashFileViewTests(AssetSubMixin, AssetFolderTrashFileViewTests):
    pass


class AssetRecycleViewTests(AssetParentMixin, BrowsingAssetViewTests, ViewTestCase):
    view_name = 'asset_recycle'

    def assertGets(self, num_folders, num_files):
        for i in range(num_folders):
            name = str(i)
            FolderAsset.objects.create(user=self.user, parent=None, name=name)
            FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=name)
            FolderAsset.objects.create(user=self.user, parent=self.parent, name=name)
            FolderAsset.objects.filter(user=self.user, name=name).update(trashed=True)
        for i in range(num_files):
            name = str(i)
            FileAsset.objects.create(user=self.user, parent=None, name=name)
            FileAsset.objects.create(user=self.user, parent=self.grand_parent, name=name)
            FileAsset.objects.create(user=self.user, parent=self.parent, name=name)
            FileAsset.objects.filter(user=self.user, name=name).update(trashed=True)
        self.powerLogin()
        html = self.get_html(kwargs=self.kwargs())
        tables = html.select('table')
        if num_folders:
            folder_trs = tables[0].select('tbody tr')
            if num_files:
                file_trs = tables[1].select('tbody tr')
            else:
                file_trs = []
        else:
            folder_trs = []
            if num_files:
                file_trs = tables[0].select('tbody tr')
            else:
                file_trs = []
        self.assertEqual(3 * num_folders, len(folder_trs))
        self.assertEqual(3 * num_files, len(file_trs))

    def testPostDisallowsAfterPowerLogin(self):
        self.powerLogin()
        response = self.post()
        self.assertEqual(405, response.status_code)


class PKAssetViewTests(SingleAssetViewTests):
    trashed = True

    def setUp(self):
        super().setUp()
        self.asset.trashed = True
        self.asset.save()

    def kwargs(self):
        return {'pk': self.asset.pk}


class AssetRestoreViewTests(AssetRecycleMixin, PKAssetViewTests, ViewTestCase):
    view_name = 'asset_restore'


class AssetFolderRestoreViewTests(AssetFolderMixin, AssetRestoreViewTests):
    pass


class AssetSubFolderRestoreViewTests(AssetSubMixin, AssetFolderRestoreViewTests):
    pass


class AssetRestoreFileViewTests(AssetFileMixin, AssetRestoreViewTests):
    view_name = 'asset_restore_file'


class AssetFolderRestoreFileViewTests(AssetFolderMixin, AssetRestoreFileViewTests):
    pass


class AssetSubFolderRestoreFileViewTests(AssetSubMixin, AssetFolderRestoreFileViewTests):
    pass


class AssetRemoveViewTests(SpecificAssetMixin, PKAssetViewTests, ViewTestCase):
    view_name = 'asset_remove'

    def substring(self):
        return self.path()

    def testExists(self):
        self.assertSource(True)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(False)


class AssetFolderRemoveViewTests(AssetFolderMixin, AssetRemoveViewTests):
    pass


class AssetSubFolderRemoveViewTests(AssetSubMixin, AssetFolderRemoveViewTests):
    pass


class AssetRemoveFileViewTests(AssetFileMixin, AssetRemoveViewTests):
    view_name = 'asset_remove_file'


class AssetFolderRemoveFileViewTests(AssetFolderMixin, AssetRemoveFileViewTests):
    pass


class AssetSubFolderRemoveFileViewTests(AssetSubMixin, AssetFolderRemoveFileViewTests):
    pass
