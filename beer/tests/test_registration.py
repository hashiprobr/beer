from django.contrib.auth import get_user_model
from django.core import mail

from . import reverse, AcceptanceSyncTestCase

User = get_user_model()


class RegistrationTests(AcceptanceSyncTestCase):
    username = 'u'
    other_username = 'ou'

    email = 'e@e.com'
    other_email = 'oe@oe.com'

    password = 'PLEGZqr2'
    other_password = '5VShJJJu'
    weak_password = 'wp'

    uidb64 = 'u'
    token = 't'

    def setUp(self):
        User.objects.create_user(self.username, self.email, self.password)

    def atLogin(self, next):
        return self.at('login', query=[('next', reverse(next))])

    def waitBlocks(self):
        self.get('index')
        self.wait(5, self.atLogin, 'index')
        self.get('password_change')
        self.wait(5, self.atLogin, 'password_change')
        self.get('password_change_done')
        self.wait(5, self.atLogin, 'password_change_done')

    def login(self, username, password):
        self.get('login')
        username_text = self.wait(5, self.driver.find_enabled, '#id_username')
        username_text.send_keys(username)
        password_text = self.wait(5, self.driver.find_enabled, '#id_password')
        password_text.send_keys(password)
        submit = self.wait(5, self.driver.find_enabled, 'input[type="submit"]')
        submit.click()

    def waitAllows(self):
        self.wait(5, self.at, 'index')
        self.get('password_change')
        self.wait(5, self.at, 'password_change')
        self.get('password_change_done')
        self.wait(5, self.at, 'password_change_done')

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
        for word in mail.outbox[0].body.strip().split():
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
        self.wait(5, self.driver.find_one, '.card > p')

    def testBlocks(self):
        self.waitBlocks()

    def testAllowsAfterLoginBlocksAfterLogout(self):
        self.login(self.username, self.password)
        self.waitAllows()
        self.get('logout')
        self.waitBlocks()

    def testBlocksAfterLoginWithWrongCredentials(self):
        self.login(self.other_username, self.password)
        self.waitBlocks()
        self.login(self.username, self.other_password)
        self.waitBlocks()

    def testChangesPassword(self):
        self.changePassword(self.password, self.other_password, self.other_password)
        self.login(self.username, self.password)
        self.waitBlocks()
        self.login(self.username, self.other_password)
        self.waitAllows()

    def testDoesNotChangePasswordWithWrongOldPassword(self):
        self.changePassword(self.other_password, self.other_password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testDoesNotChangePasswordWithDifferentNewPassword1(self):
        self.changePassword(self.password, self.password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testDoesNotChangePasswordWithDifferentNewPassword2(self):
        self.changePassword(self.password, self.other_password, self.password)
        self.login(self.username, self.other_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testDoesNotChangePasswordWithWeakNewPasswords(self):
        self.changePassword(self.password, self.weak_password, self.weak_password)
        self.login(self.username, self.weak_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testResetsPassword(self):
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.other_password)
        self.login(self.username, self.password)
        self.waitBlocks()
        self.login(self.username, self.other_password)
        self.waitAllows()

    def testDoesNotSendLinkIfEmailDoesNotExist(self):
        self.sendLink(self.other_email)
        self.assertFalse(mail.outbox)

    def testDoesNotOpenLinkWithWrongCredentials(self):
        self.sendLink(self.email)
        self.get('password_reset_confirm', kwargs={'uidb64': self.uidb64, 'token': self.token})
        self.waitMessage()

    def testDoesNotOpenLinkWithExpiredCredentials(self):
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.other_password)
        self.openLink()
        self.waitMessage()

    def testDoesNotResetPasswordWithDifferentNewPassword1(self):
        self.sendLink(self.email)
        self.resetPassword(self.password, self.other_password)
        self.login(self.username, self.other_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testDoesNotResetPasswordWithDifferentNewPassword2(self):
        self.sendLink(self.email)
        self.resetPassword(self.other_password, self.password)
        self.login(self.username, self.other_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()

    def testDoesNotResetPasswordWithWeakNewPasswords(self):
        self.sendLink(self.email)
        self.resetPassword(self.weak_password, self.weak_password)
        self.login(self.username, self.weak_password)
        self.waitBlocks()
        self.login(self.username, self.password)
        self.waitAllows()
