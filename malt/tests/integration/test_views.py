from django.contrib.auth import get_user_model

from beer.tests import ViewTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class UserViewTests:
    super_username = '35fde5760c42b7bc27494710a006918c'
    username = '528070b65f32f4f785a7e4a6ba77baf5'
    other_username = 'bba8253c7b9a27d27c8445a46c125c90'

    super_password = '5VShJJJu'
    password = 'PLEGZqr2'

    email = 'e@e.com'
    other_email = 'oe@oe.com'

    first_name = 'f'
    other_first_name = 'of'

    last_name = 'l'
    other_last_name = 'ol'

    def setUp(self):
        User.objects.create_superuser(self.super_username, password=self.super_password)
        self.user = User.objects.create_user(self.username, password=self.password)

    def kwargs(self):
        return None

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def login(self):
        self.client.login(username=self.username, password=self.password)

    def testGetRedirects(self):
        self.assertEquals(302, self.get_status(kwargs=self.kwargs()))

    def testGetForbidsAfterLogin(self):
        self.login()
        self.assertEquals(403, self.get_status(kwargs=self.kwargs()))

    def testPostRedirects(self):
        self.assertEquals(302, self.post_status(kwargs=self.kwargs()))

    def testPostForbidsAfterLogin(self):
        self.login()
        self.assertEquals(403, self.post_status(kwargs=self.kwargs()))


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
        self.post(kwargs=self.kwargs(), data=data)
        self.assertTrue(User.objects.filter(**data).exists())


class UserManageViewTests(UserViewTests, ViewTestCase):
    view_name = 'user_manage'


class SingleUserViewTests(UserViewTests):
    def kwargs(self):
        return {'pk': self.user.pk}

    def testGet(self):
        self.superLogin()
        html = self.get_html(kwargs=self.kwargs())
        h2 = html.select_one('h2')
        self.assertIn(self.username, h2.string)

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

        self.assertEquals(self.username, self.user.username)
        self.assertEquals(self.email, self.user.email)
        self.assertEquals(self.first_name, self.user.first_name)
        self.assertEquals(self.last_name, self.user.last_name)

        self.singlePost({
            'username': self.other_username,
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        })

        self.user.refresh_from_db()

        self.assertEquals(self.other_username, self.user.username)
        self.assertEquals(self.other_email, self.user.email)
        self.assertEquals(self.other_first_name, self.user.first_name)
        self.assertEquals(self.other_last_name, self.user.last_name)


class UserRemoveViewTests(SingleUserViewTests, ViewTestCase):
    view_name = 'user_remove'

    def exists(self):
        return User.objects.filter(pk=self.user.pk).exists()

    def assertExists(self):
        self.assertTrue(self.exists())

    def assertDoesNotExist(self):
        self.assertFalse(self.exists())

    def testPost(self):
        self.assertExists()
        self.singlePost()
        self.assertDoesNotExist()

    def testIdempotence(self):
        self.singlePost()
        self.singlePost()
        self.assertDoesNotExist()


class UserChangeViewTests(SingleUserViewTests):
    def power(self):
        return PowerUser.objects.filter(user=self.user).exists()

    def assertPower(self):
        self.assertTrue(self.power())
        self.assertTrue(power_cache.get(self.user))

    def assertNotPower(self):
        self.assertFalse(self.power())
        self.assertFalse(power_cache.get(self.user))


class UserPromoteViewTests(UserChangeViewTests, ViewTestCase):
    view_name = 'user_promote'

    def testPost(self):
        self.assertNotPower()
        self.singlePost()
        self.assertPower()

    def testIdempotence(self):
        self.singlePost()
        self.singlePost()
        self.assertPower()


class UserDemoteViewTests(UserChangeViewTests, ViewTestCase):
    view_name = 'user_demote'

    def testPost(self):
        PowerUser.objects.create(user=self.user)
        self.assertPower()
        self.singlePost()
        self.assertNotPower()

    def testIdempotence(self):
        PowerUser.objects.create(user=self.user)
        self.singlePost()
        self.singlePost()
        self.assertNotPower()
