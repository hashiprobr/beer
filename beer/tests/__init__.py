import os

from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Chrome, ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from channels.testing import ChannelsLiveServerTestCase

if settings.CONTAINED:
    from django.test import LiveServerTestCase as SyncLiveServerTestCase
else:
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase as SyncLiveServerTestCase


FILES_DIR = 'files'


class UnitTestCase(SimpleTestCase):
    pass


class IntegrationTestCase(TestCase):
    pass


class ViewTestCase(IntegrationTestCase):
    def html(self, urlconf=None, args=None, kwargs=None, current_app=None):
        url = reverse(self.view_name, urlconf, args, kwargs, current_app)
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        return BeautifulSoup(response.content, 'html.parser')

    def string(self, element):
        return ' '.join(element.string.strip().split())


class AcceptanceTestCase:
    @classmethod
    def is_displayed(cls, element):
        try:
            return element.is_displayed()
        except StaleElementReferenceException:
            return False

    @classmethod
    def is_enabled(cls, element):
        try:
            return element.is_enabled()
        except StaleElementReferenceException:
            return False

    @classmethod
    def find_one(cls, parent, selector):
        try:
            return parent.find_element_by_css_selector(selector)
        except StaleElementReferenceException:
            return None

    @classmethod
    def find_displayed(cls, parent, selector):
        element = cls.find_one(parent, selector)
        if element is not None:
            if not cls.is_displayed(element):
                element = None
        return element

    @classmethod
    def find_enabled(cls, parent, selector):
        element = cls.find_one(parent, selector)
        if element is not None:
            if not cls.is_displayed(element) or not cls.is_enabled(element):
                element = None
        return element

    @classmethod
    def find(cls, parent, selector):
        try:
            return parent.find_elements_by_css_selector(selector)
        except StaleElementReferenceException:
            return []

    @classmethod
    def find_at_least(cls, parent, length, selector):
        elements = cls.find(parent, selector)
        if len(elements) < length:
            elements.clear()
        return elements

    @classmethod
    def find_exactly(cls, parent, length, selector):
        elements = cls.find(parent, selector)
        if len(elements) != length:
            elements.clear()
        return elements

    @classmethod
    def find_at_most(cls, parent, length, selector):
        elements = cls.find(parent, selector)
        if len(elements) > length:
            elements.clear()
        return elements

    @classmethod
    def extend(cls, element):
        if element is not None:
            element.is_displayed = lambda: cls.is_displayed(element)
            element.is_enabled = lambda: cls.is_enabled(element)
            element.find_one = lambda selector: cls.extend(cls.find_one(element, selector))
            element.find_displayed = lambda selector: cls.extend(cls.find_displayed(element, selector))
            element.find_enabled = lambda selector: cls.extend(cls.find_enabled(element, selector))
            element.find = lambda selector: [cls.extend(child) for child in cls.find(element, selector)]
            element.find_at_least = lambda length, selector: [cls.extend(child) for child in cls.find_at_least(element, length, selector)]
            element.find_exactly = lambda length, selector: [cls.extend(child) for child in cls.find_exactly(element, length, selector)]
            element.find_at_most = lambda length, selector: [cls.extend(child) for child in cls.find_at_most(element, length, selector)]
        return element

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        if settings.HEADLESS:
            options.add_argument('headless')
            options.add_argument('no-sandbox')
        cls.driver = cls.extend(Chrome(chrome_options=options))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def url(self, view_name, urlconf=None, args=None, kwargs=None, current_app=None):
        return self.live_server_url + reverse(view_name, urlconf, args, kwargs, current_app)

    def get(self, view_name, urlconf=None, args=None, kwargs=None, current_app=None):
        self.driver.get(self.url(view_name, urlconf, args, kwargs, current_app))

    def at(self, url):
        return self.driver.current_url == url

    def open(self):
        self.driver.execute_script("window.open('about:blank', '_blank');")

    def close(self):
        self.driver.execute_script("window.close();")

    def switch(self, index):
        self.driver.switch_to_window(self.driver.window_handles[index])

    def chains(self):
        return ActionChains(self.driver)

    def wait(self, timeout, condition, *args):
        return WebDriverWait(self.driver, timeout).until(lambda driver: condition(*args), 'Exceeded {} seconds'.format(timeout))

    def text(self, element):
        return ' '.join(element.text.strip().split())

    def files_dir(self, __file__):
        path = os.path.abspath(__file__)
        dir = os.path.dirname(path)
        name = os.path.basename(path)
        return os.path.join(dir, FILES_DIR, name[5:-3])


class AcceptanceSyncTestCase(AcceptanceTestCase, SyncLiveServerTestCase):
    pass


class AcceptanceAsyncTestCase(AcceptanceTestCase, ChannelsLiveServerTestCase):
    serve_static = not settings.CONTAINED
