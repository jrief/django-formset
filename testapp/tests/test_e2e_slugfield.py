import pytest
from playwright.sync_api import expect

from django.urls import path

from formset.views import FormView

from testapp.forms.article import ArticleForm

from .utils import get_javascript_catalog


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class=ArticleForm
    success_url = '/success'


urlpatterns = [
    path('new_article', DemoFormView.as_view(), name='new_article'),
    path('current_article', DemoFormView.as_view(initial={'slug': "foo-bar"}), name='current_article'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_article'])
def test_slug_field(page, viewname):
    title_field = page.locator('django-formset input[name="title"]')
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.locator('django-formset input[name="slug"]')
    assert slug_field.evaluate('elem => elem.value') == ""
    title_field.type("Falsches 'Üben' von Xylophonmusik quält jeden größeren Zwerg.")
    assert slug_field.evaluate('elem => elem.value') == "falsches-uben-von-xylophonmusik-qualt-jeden-grosseren-zwerg"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['current_article'])
def test_initialized_slug_field(page, viewname):
    title_field = page.locator('django-formset input[name="title"]')
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.locator('django-formset input[name="slug"]')
    assert slug_field.evaluate('elem => elem.value') == "foo-bar"
    title_field.type("BAR foo")
    assert slug_field.evaluate('elem => elem.value') == "foo-bar"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_article'])
def test_invalid_slug_field(page, viewname):
    title_field = page.locator('django-formset input[name="title"]')
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.locator('django-formset input[name="slug"]')
    assert slug_field.evaluate('elem => elem.value') == ""
    submit_button = page.locator('django-formset button[df-click]').first
    submit_button.click()
    expect(page.locator('django-formset input[name="title"]:valid')).not_to_be_visible()
    expect(page.locator('django-formset input[name="slug"]:valid')).not_to_be_visible()
    title_field.type("A")
    expect(page.locator('django-formset input[name="title"]:valid')).to_be_visible()
    expect(page.locator('django-formset input[name="title"]:valid')).to_be_visible()
