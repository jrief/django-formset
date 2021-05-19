import json
import pytest
from time import sleep

from django.forms import fields, Form
from django.urls import path

from formset.views import FormsetView


class SampleForm(Form):
    name = 'sample_form'
    enter = fields.CharField()


views = {
    f'test_button_{ctr}': FormsetView.as_view(
        template_name='tests/form_with_button.html',
        form_class=SampleForm,
        success_url='/success',
        extra_context={'click_actions': click_actions, 'auto_disable': False},
    )
    for ctr, click_actions in enumerate([
        'disable -> delay(100)',
        'addClass("foo") -> delay(100)',
        'removeClass("button") -> delay(100)',
        'toggleClass("button") -> delay(10) -> toggleClass("foo") -> delay(10) -> toggleClass("bar") -> delay(10) -> toggleClass("foo") -> delay(10) -> toggleClass("bar") -> delay(10)',
        'emit("my_submit")',
    ])
}
views['test_button_submit'] = FormsetView.as_view(
    template_name='tests/form_with_button.html',
    form_class=SampleForm,
    success_url='/success',
    extra_context={'click_actions': 'submit', 'auto_disable': True},
)

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_0'])
def test_button_disable(page):
    button_elem = page.query_selector('django-formset button')
    assert button_elem is not None
    assert page.query_selector('django-formset button:disabled') is None
    button_elem.click()
    assert page.query_selector('django-formset button:disabled') is not None
    sleep(0.15)
    # as a final action, <button> restores its state
    assert page.query_selector('django-formset button:disabled') is None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_1'])
def test_button_add_class(page):
    button_elem = page.query_selector('django-formset button')
    assert 'foo' not in button_elem.get_attribute('class')
    button_elem.click()
    assert 'foo' in button_elem.get_attribute('class')
    sleep(0.15)
    # as a final action, <button> restores its state
    assert 'foo' not in button_elem.get_attribute('class')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_2'])
def test_button_remove_class(page):
    button_elem = page.query_selector('django-formset button')
    assert 'button' in button_elem.get_attribute('class')
    button_elem.click()
    assert 'button' not in button_elem.get_attribute('class')
    sleep(0.15)
    # as a final action, <button> restores its state
    assert 'button' in button_elem.get_attribute('class')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_3'])
def test_button_toggle_class(page):
    formset = page.query_selector('django-formset')
    button_elem = formset.query_selector('button.button')
    assert button_elem is not None
    button_elem.click()
    button_elem = formset.wait_for_selector('button:not(.button)')
    assert button_elem is not None
    button_elem = formset.wait_for_selector('button.foo')
    assert button_elem is not None
    button_elem = formset.wait_for_selector('button.foo.bar')
    assert button_elem is not None
    button_elem = formset.wait_for_selector('button.bar:not(.foo)')
    assert button_elem is not None
    button_elem = formset.wait_for_selector('button:not(.foo):not(.bar)')
    assert button_elem is not None
    button_elem = formset.wait_for_selector('button.button')
    assert button_elem is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_4'])
def test_button_event(page, mocker):
    magic_mock = mocker.MagicMock()
    page.expose_function('handle_my_submit', lambda s: magic_mock(s))
    page.evaluate('document.addEventListener("my_submit", () => handle_my_submit("button_clicked"))')
    page.click('django-formset button')
    magic_mock.assert_called_with('button_clicked')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_autodisable(page):
    button_elem = page.query_selector('django-formset button:disabled')
    assert button_elem is not None
    input_elem = page.query_selector('django-formset #id_enter')
    assert input_elem is not None
    input_elem.type("A")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.query_selector('django-formset button:enabled')
    assert button_elem is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_submit(page, mocker):
    input_elem = page.query_selector('#id_enter')
    assert input_elem is not None
    input_elem.type("A")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.query_selector('django-formset button')
    assert button_elem is not None
    spy = mocker.spy(FormsetView, 'post')
    page.wait_for_selector('django-formset button').click()
    request = json.loads(spy.call_args.args[1].body)
    assert request['sample_form']['enter'] == "A"
