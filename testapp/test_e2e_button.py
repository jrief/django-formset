import json
import pytest
from playwright.sync_api import expect
from time import sleep
from timeit import default_timer as timer

from django.core.exceptions import ValidationError
from django.forms import fields, Form
from django.http.response import HttpResponseForbidden
from django.urls import path

from formset.views import FormView


class SampleForm(Form):
    enter = fields.CharField(min_length=2)

    def clean_enter(self):
        cd = super().clean()
        if cd['enter'] == 'invalid':
            raise ValidationError("It's invalid")
        return cd


class NativeFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class = SampleForm
    success_url = '/success'


class ForbiddenView(NativeFormView):
    def post(self, request, **kwargs):
        return HttpResponseForbidden()


views = {
    f'test_button_{ctr}': NativeFormView.as_view(
        extra_context={'click_actions': click_actions, 'auto_disable': False},
    )
    for ctr, click_actions in enumerate([
        'disable -> delay(100)',
        'addClass("foo") -> delay(100)',
        'removeClass("button") -> delay(100)',
        'toggleClass("button") -> delay(100) -> toggleClass("foo") -> delay(100) -> toggleClass("bar") -> delay(100) -> toggleClass("foo") -> delay(100) -> toggleClass("bar")',
        'emit("my_event")',
        'emit("my_event", {foo: "bar"})',
        'submit !~ scrollToError',
        'confirm("Submit?") -> submit',
    ])
}
views['test_button_submit'] = NativeFormView.as_view(
    extra_context={'click_actions': 'submit', 'auto_disable': True},
)
views['test_button_submit_with_data'] = NativeFormView.as_view(
    extra_context={'click_actions': 'submit({foo: "bar"})', 'auto_disable': True},
)
views['test_button_alert'] = ForbiddenView.as_view(
    extra_context={'click_actions': 'submit !~ alertOnError -> delay(100)'},
)

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_0'])
def test_button_disable(page, viewname):
    button = page.locator('django-formset button').first
    expect(button).not_to_be_disabled()
    button.click()
    sleep(0.02)
    expect(button).to_be_disabled()
    sleep(0.1)
    # as a final action, <button> restores its state
    expect(button).not_to_be_disabled()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_1'])
def test_button_add_class(page, viewname):
    button = page.locator('django-formset button').first
    expect(button).to_have_class('button')
    button.click()
    sleep(0.02)
    expect(button).to_have_class('button foo')
    sleep(0.1)
    # as a final action, <button> restores its state
    expect(button).to_have_class('button')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_2'])
def test_button_remove_class(page, viewname):
    button = page.locator('django-formset button').first
    expect(button).to_have_class('button')
    button.click()
    sleep(0.02)
    expect(button).not_to_have_class('button')
    sleep(0.1)
    # as a final action, <button> restores its state
    expect(button).to_have_class('button')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_3'])
def test_button_toggle_class(page, viewname):
    """
    toggleClass("button") -> delay(100) -> toggleClass("foo") -> delay(100) -> toggleClass("bar") -> delay(100) -> toggleClass("foo") -> delay(100) -> toggleClass("bar")
    """
    formset = page.locator('django-formset')
    button = formset.locator('button[auto-disable]')
    expect(button).to_have_class('button')
    start = timer()
    button.click()
    formset.locator('button[auto-disable]:not(.button)').wait_for()
    assert timer() - start < 0.1
    formset.locator('button.foo').wait_for()
    assert timer() - start > 0.1
    formset.locator('button.foo.bar').wait_for()
    assert timer() - start > 0.2
    formset.locator('button:not(.foo).bar').wait_for()
    assert timer() - start > 0.3
    formset.locator('button[auto-disable]:not(.foo.bar)').wait_for()
    assert timer() - start > 0.4
    expect(button).to_have_class('button')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_4'])
def test_button_emit_event(page, mocker, viewname):
    magic_mock = mocker.MagicMock()
    page.expose_function('handle_emit_4', lambda s: magic_mock(s))
    page.evaluate('document.addEventListener("my_event", () => handle_emit_4("button_clicked"))')
    page.click('django-formset button')
    magic_mock.assert_called_with('button_clicked')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_5'])
def test_button_emit_custom_event(page, mocker, viewname):
    magic_mock = mocker.MagicMock()
    page.expose_function('handle_emit_5', lambda s: magic_mock(s))
    page.evaluate('document.addEventListener("my_event", event => handle_emit_5(event.detail))')
    page.click('django-formset button')
    magic_mock.assert_called_with({'foo': 'bar'})


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_6'])
def test_button_scroll_to_error(page, viewname):
    input_elem = page.locator('#id_enter')
    input_elem.type("invalid")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.locator('django-formset button').first
    success_chain, reject_chain = button_elem.get_attribute('click').split('!~')
    assert 'submit' in success_chain
    assert 'scrollToError' in reject_chain
    window_handle = page.evaluate_handle('() => Promise.resolve(window)')
    assert window_handle.get_property('scrollY').json_value() == 0
    button_elem.evaluate('elem => elem.setAttribute("style", "margin-top: 1500px;")')
    button_elem.scroll_into_view_if_needed()
    assert window_handle.get_property('scrollY').json_value() > 500
    page.wait_for_selector('django-formset button').click()
    sleep(1)  # because `scrollToError` applies behavior='smooth'
    assert window_handle.get_property('scrollY').json_value() < 50


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_7'])
def test_button_confirm_accept(page, mocker, viewname):
    def handle_dialog(dialog):
        assert dialog.type == 'confirm'
        assert dialog.message == "Submit?"
        dialog.accept()

    input_elem = page.locator('#id_enter')
    input_elem.type("Is Valid")
    input_elem.evaluate('elem => elem.blur()')
    page.once('dialog', handle_dialog)
    button = page.locator('django-formset button').first
    spy = mocker.spy(FormView, 'post')
    button.click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['enter'] == "Is Valid"

@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_7'])
def test_button_confirm_dismiss(page, mocker, viewname):
    def handle_dialog(dialog):
        assert dialog.type == 'confirm'
        assert dialog.message == "Submit?"
        dialog.dismiss()

    input_elem = page.locator('#id_enter')
    input_elem.type("Is Valid")
    input_elem.evaluate('elem => elem.blur()')
    page.once('dialog', handle_dialog)
    button = page.locator('django-formset button').first
    spy = mocker.spy(FormView, 'post')
    button.click()
    assert spy.called is False


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_alert'])
def test_button_alert(page, viewname):
    def handle_dialog(dialog):
        assert dialog.type == 'alert'
        assert dialog.message == "Forbidden"
        dialog.dismiss()

    input_elem = page.locator('#id_enter')
    input_elem.type("invalid")
    input_elem.evaluate('elem => elem.blur()')
    page.once('dialog', handle_dialog)
    button = page.locator('django-formset button').first
    button.click()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_autodisable(page, viewname):
    button_elem = page.locator('django-formset button').first
    expect(button_elem).to_be_disabled()
    input_elem = page.locator('#id_enter')
    input_elem.type("BAR")
    input_elem.evaluate('elem => elem.blur()')
    expect(button_elem).to_be_enabled()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit'])
def test_button_submit(page, mocker, viewname):
    input_elem = page.locator('#id_enter')
    input_elem.type("BAR")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.locator('django-formset button').first
    spy = mocker.spy(FormView, 'post')
    button_elem.click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['enter'] == "BAR"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['test_button_submit_with_data'])
def test_button_submit_with_data(page, mocker, viewname):
    input_elem = page.locator('#id_enter')
    input_elem.type("BAR")
    input_elem.evaluate('elem => elem.blur()')
    button_elem = page.locator('django-formset button').first
    spy = mocker.spy(FormView, 'post')
    button_elem.click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['_extra']['foo'] == "bar"
    assert request['formset_data']['enter'] == "BAR"
