import json
import pytest
from time import sleep

from django.forms import fields, Form
from django.urls import path

from formset.views import FormView


class SampleForm(Form):
    name = 'sample_form'
    enter = fields.CharField()


views = {
    f'test_button_{ctr}': FormView.as_view(
        template_name='tests/form_with_button.html',
        form_class=SampleForm,
        success_url='/success',
        extra_context={'click_actions': click_actions, 'auto_disable': False},
    )
    for ctr, click_actions in enumerate([
        'disable -> delay(100)',
        'addClass("foo") -> delay(100)',
        'removeClass("button") -> delay(100)',
        'toggleClass("button") -> delay(50) -> toggleClass("foo") -> delay(50) -> toggleClass("bar") -> delay(50) -> toggleClass("foo") -> delay(50) -> toggleClass("bar") -> delay(50)',
        'emit("my_event")',
        'emit("my_event", {foo: "bar"})',
    ])
}
views['test_button_submit'] = FormView.as_view(
    template_name='tests/form_with_button.html',
    form_class=SampleForm,
    success_url='/success',
    extra_context={'click_actions': 'submit', 'auto_disable': True},
)
views['test_button_submit_with_data'] = FormView.as_view(
    template_name='tests/form_with_button.html',
    form_class=SampleForm,
    success_url='/success',
    extra_context={'click_actions': 'submit({foo: "bar"})', 'auto_disable': True},
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
    page.click('django-formset button.button')
    button_elem = page.wait_for_selector('django-formset button:not(.button)')
    assert button_elem is not None
    button_elem = page.wait_for_selector('django-formset button.foo')
    assert button_elem is not None
    button_elem = page.wait_for_selector('django-formset button.foo.bar')
    assert button_elem is not None
    button_elem = page.wait_for_selector('django-formset button.bar:not(.foo)')
    assert button_elem is not None
    button_elem = page.wait_for_selector('django-formset button:not(.foo):not(.bar)')
    assert button_elem is not None
    button_elem = page.wait_for_selector('django-formset button.button')
    assert button_elem is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_4'])
def test_button_emit_event(page, mocker):
    magic_mock = mocker.MagicMock()
    page.expose_function('handle_emit_4', lambda s: magic_mock(s))
    page.evaluate('document.addEventListener("my_event", () => handle_emit_4("button_clicked"))')
    page.click('django-formset button')
    magic_mock.assert_called_with('button_clicked')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_5'])
def test_button_emit_custom_event(page, mocker):
    magic_mock = mocker.MagicMock()
    page.expose_function('handle_emit_5', lambda s: magic_mock(s))
    page.evaluate('document.addEventListener("my_event", event => handle_emit_5(event.detail))')
    page.click('django-formset button')
    magic_mock.assert_called_with({'foo': 'bar'})


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_autodisable(page):
    button_elem = page.query_selector('django-formset button:disabled')
    assert button_elem is not None
    input_elem = page.query_selector('django-formset #sample_form_id_enter')
    assert input_elem is not None
    input_elem.type("A")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.query_selector('django-formset button:enabled')
    assert button_elem is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_submit(page, mocker):
    input_elem = page.query_selector('#sample_form_id_enter')
    assert input_elem is not None
    input_elem.type("A")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.query_selector('django-formset button')
    assert button_elem is not None
    spy = mocker.spy(FormView, 'post')
    page.wait_for_selector('django-formset button').click()
    request = json.loads(spy.call_args.args[1].body)
    assert request['sample_form']['enter'] == "A"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit_with_data'])
def test_button_submit_with_data(page, mocker):
    input_elem = page.query_selector('#sample_form_id_enter')
    assert input_elem is not None
    input_elem.type("BAR")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.query_selector('django-formset button')
    assert button_elem is not None
    spy = mocker.spy(FormView, 'post')
    page.wait_for_selector('django-formset button').click()
    request = json.loads(spy.call_args.args[1].body)
    assert request['_extra']['foo'] == "bar"
    assert request['sample_form']['enter'] == "BAR"
