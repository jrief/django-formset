import os
import pytest
from playwright.sync_api import sync_playwright

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')


class Connector:
    def __init__(self, live_server):
        print(f"\nStarting end-to-end test server at {live_server}\n")
        self.live_server = live_server

    def __enter__(self):
        def print_args(msg):
            if msg.type in ['info', 'debug']:
                return
            for arg in msg.args:
                print(arg.json_value())

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
        self.playwright.stop()


@pytest.fixture(scope='session')
def connector(live_server):
    with Connector(live_server) as connector:
        yield connector


@pytest.fixture
def locale():
    return 'en-US'


@pytest.fixture
def language():
    return 'en'


def print_args(msg):
    for arg in msg.args:
        print(arg.json_value())


@pytest.fixture
def page(connector, viewname, locale, language):
    context = connector.browser.new_context(locale=locale)
    context.add_cookies([{'name': 'django_language', 'value': language, 'domain': 'localhost', 'path': '/'}])
    page = context.new_page()
    # page.on('console', print_args)
    page.goto(connector.live_server.url + reverse(viewname))
    django_formset = page.locator('django-formset:defined')
    django_formset.wait_for()
    return page


@pytest.fixture(scope="session")
def loaded_pages_once(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', settings.BASE_DIR / 'testapp/fixtures/reporters.json', verbosity=0)
        call_command('loaddata', settings.BASE_DIR / 'testapp/fixtures/pages.json', verbosity=0)
