import pytest
from time import sleep

from django.forms import fields, Form
from django.urls import path

from formset.views import FormsetView


class SampleForm(Form):
   enter = fields.CharField()


views = {
    f'test_button_{ctr}': FormsetView.as_view(
        template_name='form_with_button.html',
        form_class=SampleForm,
        success_url='/success',
        extra_context={'click_actions': click_actions},
    )
    for ctr, click_actions in enumerate([
        'disable -> delay(100)',
        'addClass("foo") -> delay(100)',
        'removeClass("button") -> delay(100)',
    ])
}

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
