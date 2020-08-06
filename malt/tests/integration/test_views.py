from django.contrib.auth import get_user_model

from beer.tests import ViewTestCase

from ...models import PowerUser
from ...caches import power_cache

User = get_user_model()


class UserViewTests:
    super_username = '35fde5760c42b7bc27494710a006918c'
    username = '528070b65f32f4f785a7e4a6ba77baf5'

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
        user = User.objects.create_user(self.username, password=self.password)
        self.pk = user.pk

    def superLogin(self):
        self.client.login(username=self.super_username, password=self.super_password)

    def testGetRedirects(self):
        self.assertEquals(302, self.get_status(kwargs=self.default_kwargs))

    def testGetForbidsAfterLogin(self):
        self.client.login(username=self.username, password=self.password)
        self.assertEquals(403, self.get_status(kwargs=self.default_kwargs))


class SpecificUserViewTests(UserViewTests):
    default_kwargs = {'pk': 0}

    def retrieveUser(self):
        return User.objects.get(pk=self.pk)

    def specificPost(self, data=None):
        self.superLogin()
        self.post(kwargs={'pk': self.pk}, data=data)

    def testGetDoesNotFindAfterSuperLogin(self):
        self.superLogin()
        self.assertEquals(404, self.get_status(kwargs=self.default_kwargs))

    def testGet(self):
        self.superLogin()
        html = self.get_html(kwargs={'pk': self.pk})
        h2 = html.select_one('h2')
        self.assertIn(self.username, h2.string)

    def testPostRedirects(self):
        self.assertEquals(302, self.post_status(kwargs=self.default_kwargs))

    def testPostForbidsAfterLogin(self):
        self.client.login(username=self.username, password=self.password)
        self.assertEquals(403, self.post_status(kwargs=self.default_kwargs))

    def testPostDoesNotFindAfterSuperLogin(self):
        self.superLogin()
        self.assertEquals(404, self.post_status(kwargs=self.default_kwargs))


class UserManageViewTests(UserViewTests, ViewTestCase):
    view_name = 'user_manage'
    default_kwargs = None


class UserEditViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_edit'

    def testPost(self):
        user = self.retrieveUser()
        user.email = self.email
        user.first_name = self.first_name
        user.last_name = self.last_name
        user.save()

        self.assertEquals(self.email, user.email)
        self.assertEquals(self.first_name, user.first_name)
        self.assertEquals(self.last_name, user.last_name)

        self.specificPost({
            'email': self.other_email,
            'first_name': self.other_first_name,
            'last_name': self.other_last_name,
        })
        user.refresh_from_db()

        self.assertEquals(self.other_email, user.email)
        self.assertEquals(self.other_first_name, user.first_name)
        self.assertEquals(self.other_last_name, user.last_name)


class UserRemoveViewTests(SpecificUserViewTests, ViewTestCase):
    view_name = 'user_remove'

    def exists(self):
        return User.objects.filter(pk=self.pk).exists()

    def assertExists(self):
        self.assertTrue(self.exists())

    def assertDoesNotExist(self):
        self.assertFalse(self.exists())

    def testPost(self):
        self.assertExists()
        self.specificPost()
        self.assertDoesNotExist()

    def testIdempotence(self):
        self.specificPost()
        self.specificPost()
        self.assertDoesNotExist()


class UserChangeViewTests(SpecificUserViewTests):
    def power(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def assertPower(self, user):
        self.assertTrue(self.power(user))
        self.assertTrue(power_cache.get(user))

    def assertNotPower(self, user):
        self.assertFalse(self.power(user))
        self.assertFalse(power_cache.get(user))


class UserPromoteViewTests(UserChangeViewTests, ViewTestCase):
    view_name = 'user_promote'

    def testPost(self):
        user = self.retrieveUser()
        self.assertNotPower(user)
        self.specificPost()
        self.assertPower(user)

    def testIdempotence(self):
        user = self.retrieveUser()
        self.specificPost()
        self.specificPost()
        self.assertPower(user)


class UserDemoteViewTests(UserChangeViewTests, ViewTestCase):
    view_name = 'user_demote'

    def testPost(self):
        user = self.retrieveUser()
        PowerUser.objects.create(user=user)
        self.assertPower(user)
        self.specificPost()
        self.assertNotPower(user)

    def testIdempotence(self):
        user = self.retrieveUser()
        PowerUser.objects.create(user=user)
        self.specificPost()
        self.specificPost()
        self.assertNotPower(user)
