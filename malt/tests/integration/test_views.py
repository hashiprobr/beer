import os

from io import BytesIO
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from beer import public_storage
from beer.tests import ViewTestCase
from beer.utils import join

from ...models import PowerUser, FolderAsset, FileAsset
from ...caches import power_cache
from ...views import PAGE_SIZE

User = get_user_model()


class ViewTests:
    username = '1af81dab46c4d2c8'
    super_username = '35fde5760c42b7bc'
    power_username = '528070b65f32f4f7'

    password = 'p'
    super_password = 'sp'
    power_password = 'pp'

    email = 'e@e.com'

    first_name = 'f'

    last_name = 'l'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dir = cls.files_dir(__file__)

    def open(self, name):
        path = os.path.join(self.dir, name + '.txt')
        with open(path, 'rb') as file:
            content = file.read()
        return BytesIO(content)

    def createUser(self):
        return User.objects.create_user(self.username, password=self.password, email=self.email, first_name=self.first_name, last_name=self.last_name)

    def createSuperUser(self):
        return User.objects.create_superuser(self.super_username, password=self.super_password)

    def createPowerUser(self):
        power_user = User.objects.create_user(self.power_username, password=self.power_password)
        PowerUser.objects.create(user=power_user)
        return power_user

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def powerLogin(self):
        self.client.login(username=self.power_username, password=self.power_password)

    def getKwargs(self):
        return None

    def getQuery(self):
        return None

    def getData(self):
        return None

    def assertURL(self, actual, url, query=None):
        if query is None:
            expected = url
        else:
            expected = '{}?{}'.format(url, urlencode(query, safe='/'))
        self.assertEqual(expected, actual)

    def assertView(self, actual, view_name, kwargs=None, query=None):
        url = reverse(view_name, kwargs=kwargs)
        self.assertURL(actual, url, query)

    def assertGetStatus(self, query, expected):
        if query is None:
            query = self.getQuery()
        response = self.get(kwargs=self.getKwargs(), query=query)
        self.assertEqual(expected, response.status_code)
        return response

    def assertPostStatus(self, data, expected):
        if data is None:
            data = self.getData()
        response = self.post(kwargs=self.getKwargs(), data=data)
        self.assertEqual(expected, response.status_code)
        return response

    def assertGetLocation(self, query):
        response = self.assertGetStatus(query, 302)
        return response.get('Location')

    def assertPostLocation(self, data):
        response = self.assertPostStatus(data, 302)
        return response.get('Location')


class LoginViewTests(ViewTests):
    def assertBlocks(self, url):
        next = reverse(self.view_name, kwargs=self.getKwargs())
        self.assertView(url, 'login', query={'next': next})

    def assertGetForbids(self,):
        self.assertGetStatus(None, 403)

    def assertPostForbids(self):
        self.assertPostStatus(None, 403)

    def testGetBlocks(self):
        self.assertBlocks(self.assertGetLocation(None))

    def testPostBlocks(self):
        self.assertBlocks(self.assertPostLocation(None))


class SuperViewTests(LoginViewTests):
    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertGetForbids()

    def testGetForbidsAfterPowerLogin(self):
        self.powerLogin()
        self.assertGetForbids()

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertPostForbids()

    def testPostForbidsAfterPowerLogin(self):
        self.powerLogin()
        self.assertPostForbids()

    def goodLogin(self):
        self.superLogin()


class PowerViewTests(LoginViewTests):
    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertGetForbids()

    def testGetForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertGetForbids()

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertPostForbids()

    def testPostForbidsAfterSuperLogin(self):
        self.superLogin()
        self.assertPostForbids()

    def goodLogin(self):
        self.powerLogin()


class GetDisallowsMixin:
    def testGets(self):
        self.goodLogin()
        self.assertGetStatus(None, 405)


class GetGoodMixin:
    def assertGetMisses(self, query):
        self.goodLogin()
        self.assertGetStatus(query, 404)

    def assertGetRejects(self, query):
        self.goodLogin()
        self.assertGetStatus(query, 400)

    def assertGetAccepts(self, query=None):
        self.goodLogin()
        response = self.assertGetStatus(query, 200)
        return response.content

    def assertGetRedirects(self, query=None):
        self.goodLogin()
        return self.assertGetLocation(query)

    def assertGetsJSON(self, query=None):
        return self.build_json(self.assertGetAccepts(query))

    def assertGetsHTML(self, query=None):
        return self.build_html(self.assertGetAccepts(query))

    def assertGetsURL(self, expected_url, expected_query=None, query=None):
        self.assertURL(self.assertGetRedirects(query), expected_url, expected_query)

    def assertGetsView(self, expected_view_name, expected_kwargs=None, expected_query=None, query=None):
        self.assertView(self.assertGetRedirects(query), expected_view_name, expected_kwargs)


class GetAcceptsMixin(GetGoodMixin):
    def assertGets(self, query=None):
        return self.assertGetAccepts(query)


class GetRedirectsMixin(GetGoodMixin):
    def assertGets(self, query=None):
        return self.assertGetRedirects(query)


class PostDisallowsMixin:
    def testPosts(self):
        self.goodLogin()
        self.assertPostStatus(None, 405)


class PostGoodMixin:
    def assertPostMisses(self, data):
        self.goodLogin()
        self.assertPostStatus(data, 404)

    def assertPostRejects(self, data):
        self.goodLogin()
        self.assertPostStatus(data, 400)

    def assertPostAccepts(self, data=None):
        self.goodLogin()
        response = self.assertPostStatus(data, 200)
        return response.content

    def assertPostRedirects(self, data=None):
        self.goodLogin()
        return self.assertPostLocation(data)

    def assertPostsJSON(self, data=None):
        return self.build_json(self.assertPostAccepts(data))

    def assertPostsHTML(self, data=None):
        return self.build_html(self.assertPostAccepts(data))

    def assertPostsURL(self, expected_url, expected_query=None, data=None):
        self.assertURL(self.assertPostRedirects(data), expected_url, expected_query)

    def assertPostsView(self, expected_view_name, expected_kwargs=None, expected_query=None, data=None):
        self.assertView(self.assertPostRedirects(data), expected_view_name, expected_kwargs)


class PostAcceptsMixin(PostGoodMixin):
    def assertPosts(self, data=None):
        return self.assertPostAccepts(data)


class PostRedirectsMixin(PostGoodMixin):
    def assertPosts(self, data=None):
        return self.assertPostRedirects(data)


class UserViewTests(GetAcceptsMixin, PostRedirectsMixin, SuperViewTests):
    usernames = [
        'AaaDddEee',
        'aAAeEEdDD',
        'FffBbbGgg',
        'gGGbBBfFF',
        'HhhIiiCcc',
        'iIIhHHcCC',
    ]

    other_username = 'bba8253c7b9a27d2'

    other_email = 'oe@oe.com'

    other_first_name = 'of'

    other_last_name = 'ol'

    def setUp(self):
        self.user = self.createUser()
        self.createPowerUser()
        self.createSuperUser()

    def power(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def assertPower(self, user):
        self.assertTrue(self.power(user))
        self.assertTrue(power_cache.get(user))

    def assertNotPower(self, user):
        self.assertFalse(self.power(user))
        self.assertFalse(power_cache.get(user))

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


class UserManageViewTests(UserViewTests, ViewTestCase):
    view_name = 'user_manage'

    def create(self, users):
        for username, email, first_name, last_name, actual in users:
            user = User.objects.create(username=username, email=email, first_name=first_name, last_name=last_name)
            if actual:
                PowerUser.objects.create(user=user)

    def build(self, name, promote):
        return {
            'file': self.open(name),
            'domain': 'd.com',
            'promote': promote,
        }

    def getData(self):
        return self.build('one', False)

    def assertGetsFilter(self, filter, expected):
        for username in self.usernames:
            User.objects.create_user(username)
        if filter is None:
            query = None
        else:
            query = {'filter': filter}
        html = self.assertGetsHTML(query)
        trs = html.select('tbody tr')
        actual = [self.read(tr.select_one('td')) for tr in trs]
        self.assertEqual(expected, actual)

    def assertGetsPage(self, n, page, length, left, center, right):
        for i in range(n - 3):
            User.objects.create_user(str(i))
        if page is None:
            query = None
        else:
            query = {'page': page}
        html = self.assertGetsHTML(query)
        trs = html.select('tbody tr')
        caption = html.select_one('caption')
        arrows = [self.read(a) for a in caption.select('a')]
        self.assertEqual(length, len(trs))
        self.assertEqual(left, '🡨' in arrows)
        self.assertIn(center, self.read(caption))
        self.assertEqual(right, '🡪' in arrows)

    def assertPosts(self, name, promote, users):
        super().assertPosts(self.build(name, promote))
        for username, email, first_name, last_name, expected in users:
            user = self.assertExists(username, email, first_name, last_name)
            if expected:
                self.assertPower(user)
            else:
                self.assertNotPower(user)

    def testGetsWithoutFilter(self):
        self.assertGetsFilter(None, [
            self.username,
            self.super_username,
            self.power_username,
            *self.usernames,
        ])

    def testGetsWithPrefixLowerFilter(self):
        self.assertGetsFilter('aaa', [
            'AaaDddEee',
            'aAAeEEdDD',
        ])

    def testGetsWithPrefixUpperFilter(self):
        self.assertGetsFilter('AAA', [
            'AaaDddEee',
            'aAAeEEdDD',
        ])

    def testGetsWithMiddleLowerFilter(self):
        self.assertGetsFilter('bbb', [
            'FffBbbGgg',
            'gGGbBBfFF',
        ])

    def testGetsWithMiddleUpperFilter(self):
        self.assertGetsFilter('BBB', [
            'FffBbbGgg',
            'gGGbBBfFF',
        ])

    def testGetsWithSuffixLowerFilter(self):
        self.assertGetsFilter('ccc', [
            'HhhIiiCcc',
            'iIIhHHcCC',
        ])

    def testGetsWithSuffixUpperFilter(self):
        self.assertGetsFilter('CCC', [
            'HhhIiiCcc',
            'iIIhHHcCC',
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


class UserDataMixin:
    def getData(self):
        return {
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        }


class UserAddViewTests(UserDataMixin, UserViewTests, ViewTestCase):
    view_name = 'user_add'

    def testGets(self):
        self.assertGets()

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.other_username)

    def testPosts(self):
        self.assertPosts()
        self.assertExists(self.other_username, self.other_email, self.other_first_name, self.other_last_name)


class SpecificUserViewTests(UserViewTests):
    def getKwargs(self):
        return {'pk': self.user.pk}

    def testGets(self):
        html = self.assertGetsHTML()
        h2 = html.select_one('h2')
        self.assertIn(self.user.get_username(), self.read(h2))


class UserEditViewTests(UserDataMixin, SpecificUserViewTests, ViewTestCase):
    view_name = 'user_edit'

    def testKeeps(self):
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


class UploadViewTests(PowerViewTests):
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
        self.upper_name = (FileAsset.name.field.max_length + 1) * 'n'

        self.createUser()
        self.createSuperUser()
        self.user = self.createPowerUser()

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.grand_parent_name)
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=self.parent_name)

    def mock(self):
        return BytesIO(b'c')


class PostUploadViewTests(GetDisallowsMixin, UploadViewTests):
    pass


class UploadManageViewTests(PostAcceptsMixin, PostUploadViewTests, ViewTestCase):
    view_name = 'upload_manage'

    def getData(self):
        return {
            'method': 'code',
            'name': self.name,
        }

    def exists(self, parent):
        return FileAsset.objects.filter(user=self.user, parent=parent, name=self.name).exists()

    def update(self, data):
        data['method'] = 'asset'
        try:
            data['path'] = join(data['path'])
        except KeyError:
            pass

    def assertPostsAsset(self, data, parent):
        self.update(data)
        self.assertPosts(data)
        self.assertTrue(self.exists(parent))

    def assertPostMissesAsset(self, data):
        self.update(data)
        self.assertPostMisses(data)

    def assertPostRejectsAsset(self, data):
        self.update(data)
        self.assertPostRejects(data)

    def testPostRejectsWithoutMethod(self):
        self.assertPostRejects({
            'mock': 'code',
            'name': self.name,
        })

    def testPostRejectsWithoutName(self):
        self.assertPostRejects({
            'method': 'code',
            'mock': self.name,
        })

    def testPostMissesWithWrongMethod(self):
        self.assertPostMisses({
            'method': 'mock',
            'name': self.name,
        })

    def testPostsCode(self):
        self.assertPosts({
            'method': 'code',
            'name': self.name,
        })

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
        self.assertPostRejectsAsset({
            'name': self.empty_name,
            'path': [self.grand_parent_name, self.parent_name],
        })

    def testPostRejectsAssetWithWhiteName(self):
        self.assertPostRejectsAsset({
            'name': self.white_name,
            'path': [self.grand_parent_name, self.parent_name],
        })

    def testPostRejectsAssetWithSlashName(self):
        self.assertPostRejectsAsset({
            'name': self.slash_name,
            'path': [self.grand_parent_name, self.parent_name],
        })

    def testPostRejectsAssetWithUpperName(self):
        self.assertPostRejectsAsset({
            'name': self.upper_name,
            'path': [self.grand_parent_name, self.parent_name],
        })

    def testPostRejectsAssetWithoutPath(self):
        self.assertPostRejectsAsset({
            'name': self.name,
            'mock': [self.grand_parent_name, self.parent_name],
        })

    def testPostMissesAssetWithWrongPath(self):
        self.assertPostMissesAsset({
            'name': self.name,
            'path': [self.parent_name, self.grand_parent_name],
        })

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


class UploadCodeViewTests(PostUploadViewTests):
    view_name = 'upload_code'

    def testPosts(self):
        self.assertPosts()


class UploadCodeAcceptsViewTests(PostAcceptsMixin, UploadCodeViewTests, ViewTestCase):
    pass


class UploadCodeRedirectsViewTests(PostRedirectsMixin, UploadCodeViewTests, ViewTestCase):
    def getData(self):
        return {
            'file': self.open('yeast'),
            'date': 0,
        }


class UploadAssetViewTests(PostRedirectsMixin, PostUploadViewTests, ViewTestCase):
    view_name = 'upload_asset'

    def getData(self):
        return {
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
        }

    def exists(self):
        return public_storage.exists(self.key)

    def assertMissesOrPosts(self, data):
        if settings.CONTAINED:
            self.assertPostMisses(data)
        else:
            self.assertPosts(data)
            self.assertTrue(self.exists())

    def assertMissesOrRejects(self, data):
        if settings.CONTAINED:
            self.assertPostMisses(data)
        else:
            self.assertPostRejects(data)

    def testDoesNotExist(self):
        self.assertFalse(self.exists())

    def testPosts(self):
        self.assertMissesOrPosts({
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
        })

    def testPostRejectsWithoutKey(self):
        self.assertMissesOrRejects({
            'mock': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
        })

    def testPostRejectsWithEmptyKey(self):
        self.assertMissesOrRejects({
            'key': self.empty_key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
        })

    def testPostRejectsWithWhiteKey(self):
        self.assertMissesOrRejects({
            'key': self.white_key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
        })

    def testPostRejectsWithoutRedirectURL(self):
        self.assertMissesOrRejects({
            'key': self.key,
            'mock': self.redirect_url,
            'file': self.mock(),
        })

    def testPostRejectsWithWrongRedirectURL(self):
        self.assertMissesOrRejects({
            'key': self.key,
            'success_action_redirect': 'mock',
            'file': self.mock(),
        })

    def testPostRejectsWithoutFile(self):
        self.assertMissesOrRejects({
            'key': self.key,
            'success_action_redirect': self.redirect_url,
        })

    def testPostRejectsWithTwoFiles(self):
        self.assertMissesOrRejects({
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'file': self.mock(),
            'mock': self.mock(),
        })

    def testPostRejectsIfInputNotFile(self):
        self.assertMissesOrRejects({
            'key': self.key,
            'success_action_redirect': self.redirect_url,
            'mock': self.mock(),
        })


class UploadAssetConfirmViewTests(PostDisallowsMixin, GetRedirectsMixin, UploadViewTests, ViewTestCase):
    view_name = 'upload_asset_confirm'

    def create(self, parent):
        file_asset = FileAsset.objects.create(user=self.user, parent=parent, name=self.name)
        file_asset.uid = self.uid
        file_asset.save()
        key = file_asset.key()
        file = self.mock()
        public_storage.save(key, file)
        return file_asset

    def getData(self):
        self.create(self.parent)
        return {
            'key': self.uid,
        }

    def assertGets(self, parent):
        file_asset = self.create(parent)
        super().assertGets({
            'key': self.uid,
        })
        file_asset.refresh_from_db()
        self.assertTrue(file_asset.active)

    def testKeeps(self):
        self.assertFalse(self.create(None).active)
        self.assertFalse(self.create(self.grand_parent).active)
        self.assertFalse(self.create(self.parent).active)

    def testGets(self):
        self.assertGets(self.parent)

    def testGetsWithNoneParent(self):
        self.assertGets(None)

    def testGetsWithGrandParent(self):
        self.assertGets(self.grand_parent)

    def testGetMissesWithoutFileAsset(self):
        self.assertGetMisses({
            'key': self.uid,
        })

    def testGetRejectsWithoutKey(self):
        self.create(self.parent)
        self.assertGetRejects({
            'mock': self.uid,
        })

    def testGetMissesWithWrongKey(self):
        self.create(self.parent)
        self.assertGetMisses({
            'key': 'mock',
        })


class AssetViewTests(PowerViewTests):
    trashed = False
    Asset = FolderAsset

    grand_parent_name = '1cb3bba7d6539fd8'
    other_grand_parent_name = '3d2c0bba01bffa85'
    parent_name = '58ecf11ab31c9e77'
    other_parent_name = '6bdc514167a3db99'
    child_name = '8a8e367c2ebfd83a'
    grand_child_name = '9cb85ee9f59d0296'
    name = 'bca0ab9eb8383fda'
    other_name = 'eceeae86d5766723'

    def setUp(self):
        self.createUser()
        self.createSuperUser()
        self.user = self.createPowerUser()

    def getParent(self):
        return None

    def getNames(self):
        return []

    def exists(self, parent, name, trashed):
        return self.Asset.objects.filter(user=self.user, parent=parent, name=name, trashed=trashed).exists()

    def existsBase(self, trashed):
        return self.exists(self.getParent(), self.name, trashed)

    def assertSource(self, expected):
        self.assertEqual(expected, self.existsBase(self.trashed))


class BrowsingAssetViewTests(GetAcceptsMixin, AssetViewTests):
    def select(self, num_folders, num_files):
        html = self.assertGetsHTML()
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
        return folder_trs, file_trs

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
    def getParent(self):
        return self.grand_parent

    def getNames(self):
        return [self.grand_parent_name]


class AssetSubMixin:
    def getParent(self):
        return self.parent

    def getNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetManageViewTests(PostRedirectsMixin, BrowsingAssetViewTests, ViewTestCase):
    view_name = 'asset_manage'

    def getData(self):
        return {
            'name': self.name,
        }

    def assertGets(self, num_folders, num_files):
        for i in range(num_folders):
            FolderAsset.objects.create(user=self.user, parent=self.getParent(), name=str(i))
        for i in range(num_files):
            FileAsset.objects.create(user=self.user, parent=self.getParent(), name=str(i))
        folder_trs, file_trs = self.select(num_folders, num_files)
        self.assertEqual(num_folders, len(folder_trs))
        self.assertEqual(num_files, len(file_trs))

    def testDoesNotExist(self):
        self.assertSource(False)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(True)


class AssetFolderManageViewTests(AssetFolderMixin, AssetGrandParentMixin, AssetManageViewTests):
    view_name = 'asset_manage_folder'

    def getKwargs(self):
        return {'path': join(self.getNames())}


class AssetSubFolderManageViewTests(AssetSubMixin, AssetParentMixin, AssetFolderManageViewTests):
    pass


class SingleAssetViewTests(AssetParentMixin, AssetViewTests):
    def setUp(self):
        super().setUp()
        self.other_grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name=self.other_grand_parent_name)
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name=self.other_parent_name)
        self.child = FolderAsset.objects.create(user=self.user, parent=self.parent, name=self.child_name)
        self.grand_child = FolderAsset.objects.create(user=self.user, parent=self.child, name=self.grand_child_name)
        self.asset = self.Asset.objects.create(user=self.user, parent=self.getParent(), name=self.name)

    def getPath(self):
        return join([*self.getNames(), self.name])


class PathAssetViewTests(SingleAssetViewTests):
    def getKwargs(self):
        return {'path': self.getPath()}


class SpecificAssetMixin(GetAcceptsMixin):
    def getPattern(self):
        return self.name

    def testGets(self):
        html = self.assertGetsHTML()
        h2 = html.select_one('h2')
        self.assertIn(self.getPattern(), self.read(h2))


class AssetUpdateMixin:
    def testKeeps(self):
        self.assertSource(True)
        self.assertTarget(False)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(False)
        self.assertTarget(True)


class AssetFileMixin:
    Asset = FileAsset


class AssetMoveViewTests(PostRedirectsMixin, SpecificAssetMixin, PathAssetViewTests):
    view_name = 'asset_move'

    def getTargetParent(self):
        return None

    def getTargetNames(self):
        return []

    def getTargetName(self):
        return self.name

    def getData(self):
        return {
            'path': join([*self.getTargetNames(), self.getTargetName()]),
        }

    def assertTarget(self, expected):
        self.assertEqual(expected, self.exists(self.getTargetParent(), self.getTargetName(), self.trashed))


class AssetMoveFileMixin(AssetFileMixin):
    view_name = 'asset_move_file'


class AssetMoveNothingViewTests(AssetMoveViewTests, ViewTestCase):
    def testKeeps(self):
        self.assertSource(True)
        self.assertTarget(True)

    def testPosts(self):
        self.assertPosts()
        self.assertSource(True)
        self.assertTarget(True)


class AssetMoveNothingFileViewTests(AssetMoveFileMixin, AssetMoveNothingViewTests):
    pass


class AssetFolderMoveNothingViewTests(AssetFolderMixin, AssetMoveNothingViewTests):
    def getTargetParent(self):
        return self.grand_parent

    def getTargetNames(self):
        return [self.grand_parent_name]


class AssetFolderMoveNothingFileViewTests(AssetMoveFileMixin, AssetFolderMoveNothingViewTests):
    pass


class AssetSubFolderMoveNothingViewTests(AssetSubMixin, AssetFolderMoveNothingViewTests):
    def getTargetParent(self):
        return self.parent

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetSubFolderMoveNothingFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveNothingViewTests):
    pass


class AssetMoveSomethingViewTests(AssetUpdateMixin, AssetMoveViewTests):
    pass


class AssetMoveNameViewTests(AssetMoveSomethingViewTests, ViewTestCase):
    def getTargetName(self):
        return self.other_name


class AssetMoveNameFileViewTests(AssetMoveFileMixin, AssetMoveNameViewTests):
    pass


class AssetMoveDownOneViewTests(AssetMoveSomethingViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.grand_parent

    def getTargetNames(self):
        return [self.grand_parent_name]


class AssetMoveDownOneFileViewTests(AssetMoveFileMixin, AssetMoveDownOneViewTests):
    pass


class AssetMoveDownTwoViewTests(AssetMoveSomethingViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.parent

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetMoveDownTwoViewTests):
    pass


class AssetFolderMoveViewTests(AssetFolderMixin, AssetMoveSomethingViewTests):
    pass


class AssetFolderMoveNameViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.grand_parent

    def getTargetNames(self):
        return [self.grand_parent_name]

    def getTargetName(self):
        return self.other_name


class AssetFolderMoveNameFileViewTests(AssetMoveFileMixin, AssetFolderMoveNameViewTests):
    pass


class AssetFolderMoveUpViewTests(AssetFolderMoveViewTests, ViewTestCase):
    pass


class AssetFolderMoveUpFileViewTests(AssetMoveFileMixin, AssetFolderMoveUpViewTests):
    pass


class AssetFolderMoveSideViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.other_grand_parent

    def getTargetNames(self):
        return [self.other_grand_parent_name]


class AssetFolderMoveSideFileViewTests(AssetMoveFileMixin, AssetFolderMoveSideViewTests):
    pass


class AssetFolderMoveDownOneViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.parent

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name]


class AssetFolderMoveDownOneFileViewTests(AssetMoveFileMixin, AssetFolderMoveDownOneViewTests):
    pass


class AssetFolderMoveDownTwoViewTests(AssetFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.child

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name]


class AssetFolderMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetFolderMoveDownTwoViewTests):
    pass


class AssetSubFolderMoveViewTests(AssetSubMixin, AssetFolderMoveViewTests):
    pass


class AssetSubFolderMoveNameViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.parent

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name]

    def getTargetName(self):
        return self.other_name


class AssetSubFolderMoveNameFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveNameViewTests):
    pass


class AssetSubFolderMoveUpOneViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.grand_parent

    def getTargetNames(self):
        return [self.grand_parent_name]


class AssetSubFolderMoveUpOneFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveUpOneViewTests):
    pass


class AssetSubFolderMoveUpTwoViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    pass


class AssetSubFolderMoveUpTwoFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveUpTwoViewTests):
    pass


class AssetSubFolderMoveSideViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.other_parent

    def getTargetNames(self):
        return [self.grand_parent_name, self.other_parent_name]


class AssetSubFolderMoveSideFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveSideViewTests):
    pass


class AssetSubFolderMoveDownOneViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.child

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name]


class AssetSubFolderMoveDownOneFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveDownOneViewTests):
    pass


class AssetSubFolderMoveDownTwoViewTests(AssetSubFolderMoveViewTests, ViewTestCase):
    def getTargetParent(self):
        return self.grand_child

    def getTargetNames(self):
        return [self.grand_parent_name, self.parent_name, self.child_name, self.grand_child_name]


class AssetSubFolderMoveDownTwoFileViewTests(AssetMoveFileMixin, AssetSubFolderMoveDownTwoViewTests):
    pass


class AssetRecycleMixin(AssetUpdateMixin, PostRedirectsMixin, GetDisallowsMixin):
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


class AssetRecycleViewTests(AssetParentMixin, PostDisallowsMixin, BrowsingAssetViewTests, ViewTestCase):
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
        folder_trs, file_trs = self.select(num_folders, num_files)
        self.assertEqual(3 * num_folders, len(folder_trs))
        self.assertEqual(3 * num_files, len(file_trs))


class PKAssetViewTests(SingleAssetViewTests):
    trashed = True

    def setUp(self):
        super().setUp()
        self.asset.trashed = True
        self.asset.save()

    def getKwargs(self):
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


class AssetRemoveViewTests(PostRedirectsMixin, SpecificAssetMixin, PKAssetViewTests, ViewTestCase):
    view_name = 'asset_remove'

    def getPattern(self):
        return self.getPath()

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
