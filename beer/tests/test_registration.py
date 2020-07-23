from django.contrib.auth.models import User
from django.core import mail

from . import AcceptanceSyncTestCase, reverse


class AuthenticationTests(AcceptanceSyncTestCase):
    username = 'u'
    other_username = 'ou'

    email = 'e@e.com'
    other_email = 'oe@oe.com'

    password = 'PLEGZqr224'
    other_password = '5VShJJJurW'
    weak_password = 'wp'

    uidb64 = 'u'
    token = 't'


    def atLogin(self, next):
        return self.at('{}?next={}'.format(self.url('login'), reverse(next)))

    def waitBlocks(self):
        self.get('index')
        self.wait(5, self.atLogin, 'index')
        self.get('password_change')
        self.wait(5, self.atLogin, 'password_change')

    def login(self, username, password):
        self.get('login')
        username_text = self.wait(5, self.driver.find_enabled, '#id_username')
        username_text.send_keys(username)
        password_text = self.wait(5, self.driver.find_enabled, '#id_password')
        password_text.send_keys(password)
        submit = self.wait(5, self.driver.find_enabled, 'input[type="submit"]')
        submit.click()

    def waitAllows(self):
        self.wait(5, self.at, self.url('index'))
        self.get('password_change')
        self.wait(5, self.at, self.url('password_change'))

    def changePassword(self, old_password, new_password1, new_password2):
        self.login(self.username, self.password)
        self.get('password_change')
        old_password_text = self.wait(5, self.driver.find_enabled, '#id_old_password')
        old_password_text.send_keys(old_password)
        new_password1_text = self.wait(5, self.driver.find_enabled, '#id_new_password1')
        new_password1_text.send_keys(new_password1)
        new_password2_text = self.wait(5, self.driver.find_enabled, '#id_new_password2')
        new_password2_text.send_keys(new_password2)
        submit = self.wait(5, self.driver.find_enabled, 'input[type="submit"]')
        submit.click()
        self.get('logout')

    def sendLink(self, email):
        self.get('password_reset')
        email_text = self.wait(5, self.driver.find_enabled, '#id_email')
        email_text.send_keys(email)
        submit = self.wait(5, self.driver.find_enabled, 'input[type="submit"]')
        submit.click()

    def openLink(self):
        for word in mail.outbox[0].body.split():
            if word.startswith('http'):
                self.driver.get(word)
                return

    def resetPassword(self, new_password1, new_password2):
        self.openLink()
        new_password1_text = self.wait(5, self.driver.find_enabled, '#id_new_password1')
        new_password1_text.send_keys(new_password1)
        new_password2_text = self.wait(5, self.driver.find_enabled, '#id_new_password2')
        new_password2_text.send_keys(new_password2)
        submit = self.wait(5, self.driver.find_enabled, 'input[type="submit"]')
        submit.click()

    def waitMessage(self):
        self.wait(5, self.driver.find_one, 'p.small')


    def testBlocks(self):
        self.waitBlocks()

    def testAllowsAfterLoggedInBlocksAfterLoggedOut(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.login(self.username, self.password)
        self.waitAllows()
        self.get('logout')
        self.waitBlocks()

    def testBlocksAfterLoggedInWithWrongNonExistingCredentials(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.login(self.other_username, self.password)
        self.waitBlocks()
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testBlocksAfterLoggedInWithWrongButExistingPassword(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        other_user = User.objects.create_user(self.other_username, self.email, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testChangesPassword(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.changePassword(self.password, self.other_password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitAllows()

    def testDoesNotChangePasswordWithWrongOldPassword(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.changePassword(self.other_password, self.other_password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testDoesNotChangePasswordWithDifferentNewPassword1(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.changePassword(self.password, self.password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testDoesNotChangePasswordWithDifferentNewPassword2(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.changePassword(self.password, self.other_password, self.password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testDoesNotChangePasswordWithWeakNewPasswords(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.changePassword(self.password, self.weak_password, self.weak_password)
        self.login(self.username, self.weak_password)
        self.waitBlocks()

    def testResetsPassword(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitAllows()

    def testDoesNotSendLinkIfEmailDoesNotExist(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.other_email)
        self.assertFalse(mail.outbox)

    def testDoesNotOpenLinkWithWrongCredentials(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.driver.get(self.url('password_reset_confirm', args=[self.uidb64, self.token]))
        self.waitMessage()

    def testDoesNotOpenLinkWithExpiredCredentials(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.other_password)
        self.openLink()
        self.waitMessage()

    def testDoesNotResetPasswordWithDifferentNewPassword1(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.resetPassword(self.password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testDoesNotResetPasswordWithDifferentNewPassword2(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.password)
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testDoesNotResetPasswordWithWeakNewPasswords(self):
        user = User.objects.create_user(self.username, self.email, self.password)
        self.sendLink(self.email)
        self.resetPassword(self.weak_password, self.weak_password)
        self.login(self.username, self.weak_password)
        self.waitBlocks()
