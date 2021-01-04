import json
import os

from urllib.parse import urlencode

from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Chrome, ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from channels.testing import ChannelsLiveServerTestCase

if settings.CONTAINED:
    from django.test import LiveServerTestCase as SyncLiveServerTestCase
else:
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase as SyncLiveServerTestCase

from .. import public_storage, private_storage
from ..utils import collapse


FILES_DIR = 'files'


class FilesMixin:
    @classmethod
    def files_dir(cls, __file__):
        path = os.path.abspath(__file__)
        dir = os.path.dirname(path)
        name = os.path.basename(path)
        return os.path.join(dir, FILES_DIR, name[5:-3])


class ClearMixin:
    def _pre_setup(self):
        private_storage.clear()
        public_storage.clear()
        super()._pre_setup()
        cache.clear()


class UnitTestCase(FilesMixin, SimpleTestCase):
    pass


class IntegrationTestCase(FilesMixin, ClearMixin, TestCase):
    pass


class ViewTestCase(IntegrationTestCase):
    def url(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        url = reverse(self.view_name, urlconf, args, kwargs, current_app)
        if query is not None:
            url = '{}?{}'.format(url, urlencode(query, safe='/'))
        return url

    def get(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        return self.client.get(self.url(urlconf, args, kwargs, current_app, query))

    def get_status(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        response = self.get(urlconf, args, kwargs, current_app, query)
        return response.status_code

    def get_html(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        response = self.get(urlconf, args, kwargs, current_app, query)
        return BeautifulSoup(response.content, 'html.parser')

    def post(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None, data=None):
        return self.client.post(self.url(urlconf, args, kwargs, current_app, query), data)

    def post_status(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None, data=None):
        response = self.post(urlconf, args, kwargs, current_app, query, data)
        return response.status_code

    def post_json(self, urlconf=None, args=None, kwargs=None, current_app=None, query=None, data=None):
        response = self.post(urlconf, args, kwargs, current_app, query, data)
        return json.loads(response.content)

    def string(self, element):
        return collapse(''.join(element.find_all(text=True)))


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
        cls.driver.at = lambda url: cls.driver.current_url == url

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def url(self, view_name, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        url = self.live_server_url + reverse(view_name, urlconf, args, kwargs, current_app)
        if query is not None:
            url = '{}?{}'.format(url, urlencode(query, safe='/'))
        return url

    def at(self, view_name, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        return self.driver.at(self.url(view_name, urlconf, args, kwargs, current_app, query))

    def get(self, view_name, urlconf=None, args=None, kwargs=None, current_app=None, query=None):
        self.driver.get(self.url(view_name, urlconf, args, kwargs, current_app, query))

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
        return collapse(element.text)


class AcceptanceSyncTestCase(FilesMixin, ClearMixin, AcceptanceTestCase, SyncLiveServerTestCase):
    pass


class AcceptanceAsyncTestCase(FilesMixin, ClearMixin, AcceptanceTestCase, ChannelsLiveServerTestCase):
    serve_static = not settings.CONTAINED
