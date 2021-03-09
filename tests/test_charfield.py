import pytest
import json

from django.forms import CharField, Form
from django.urls import path

from formset.views import FormsetView


class SubscribeForm(Form):
    name = 'subscribe'

    last_name = CharField(
        label="Last name",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
        initial='J',
    )


urlpatterns = [
    path('form1', FormsetView.as_view(
        template_name='form.html',
        form_class=SubscribeForm,
        success_url='/success',
        extra_context={'force_submission': True, 'withhold_messages': True},
    ), name='form1'),
    path('form2', FormsetView.as_view(
        template_name='form.html',
        form_class=SubscribeForm,
        success_url='/success',
        extra_context={'force_submission': False, 'withhold_messages': False},
    ), name='form2'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['form1'])
def test_screenshot(page):
    page.screenshot(path="example1.png")
    assert True


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['form2'])
def test_fixture(page, mocker):
    page.screenshot(path="example2.png")
    valid_form = page.query_selector('django-formset form:valid')
    assert valid_form is None
    invalid_form = page.query_selector('django-formset form:invalid')
    assert invalid_form is not None
    spy = mocker.spy(FormsetView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request['subscribe']['last_name'] == 'J'
    error_message = page.query_selector('django-formset .dj-errorlist > .dj-placeholder').inner_text()
    assert error_message == "Ensure this value has at least 2 characters (it has 1)."
