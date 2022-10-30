import pytest

from django.urls import path

from formset.views import FormView

from .forms.article import ArticleForm


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class=ArticleForm
    success_url = '/success'


urlpatterns = [
    path('new_article', DemoFormView.as_view(), name='new_article'),
    path('current_article', DemoFormView.as_view(initial={'slug': "foo-bar"}), name='current_article'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_article'])
def test_slug_field(page, viewname):
    title_field = page.query_selector('django-formset input[name="title"]')
    assert title_field is not None
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.query_selector('django-formset input[name="slug"]')
    assert slug_field is not None
    assert slug_field.evaluate('elem => elem.value') == ""
    title_field.type("Falsches 'Üben' von Xylophonmusik quält jeden größeren Zwerg.")
    assert slug_field.evaluate('elem => elem.value') == "falsches-uben-von-xylophonmusik-qualt-jeden-grosseren-zwerg"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['current_article'])
def test_initialized_slug_field(page, viewname):
    title_field = page.query_selector('django-formset input[name="title"]')
    assert title_field is not None
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.query_selector('django-formset input[name="slug"]')
    assert slug_field is not None
    assert slug_field.evaluate('elem => elem.value') == "foo-bar"
    title_field.type("BAR foo")
    assert slug_field.evaluate('elem => elem.value') == "foo-bar"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_article'])
def test_invalid_slug_field(page, viewname):
    title_field = page.query_selector('django-formset input[name="title"]')
    assert title_field is not None
    assert title_field.evaluate('elem => elem.value') == ""
    slug_field = page.query_selector('django-formset input[name="slug"]')
    assert slug_field is not None
    submit_button = page.query_selector('django-formset button[click]')
    submit_button.click()
    assert page.query_selector('django-formset input[name="title"]:valid') is None
    assert page.query_selector('django-formset input[name="slug"]:valid') is None
    title_field.type("A")
    assert page.query_selector('django-formset input[name="title"]:invalid') is None
    assert page.query_selector('django-formset input[name="slug"]:invalid') is None
