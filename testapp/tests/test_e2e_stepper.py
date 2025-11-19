import json
import pytest
from playwright.sync_api import expect
from time import sleep

from django.urls import path

from formset.views import FormCollectionView

from testapp.forms.checkout import CheckoutCollection

from .utils import ContextMixin, get_javascript_catalog


class StepperCollectionView(ContextMixin, FormCollectionView):
    collection_class = CheckoutCollection
    template_name = 'testapp/form-collection.html'
    success_url = '/success'


urlpatterns = [
    path('empty_stepper', StepperCollectionView.as_view(), name='empty_stepper'),
    path('empty_stepper_forced', StepperCollectionView.as_view(
        extra_context={'force_submission': True},
    ), name='empty_stepper_forced'),
    path('prefilled_stepper', StepperCollectionView.as_view(
        initial={'contact': {'first_name': "John", 'last_name': "Doe"}}
    ), name='prefilled_stepper'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['empty_stepper', 'empty_stepper_forced'])
def test_steps_remain_inactive(page, mocker, viewname):
    stepper_collection = page.locator('django-stepper-collection')
    expect(stepper_collection).to_be_visible()

    step_items = stepper_collection.locator('ul.stepper-horizontal > li.stepper-step').all()
    assert len(step_items) == 3
    expect(step_items[0]).to_have_attribute('aria-current', 'step')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_class('stepper-step')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')

    collections = stepper_collection.locator('django-form-collection').all()
    assert len(collections) == 3
    expect(collections[0]).to_have_attribute('aria-current', 'step')
    expect(collections[0]).to_be_visible()
    expect(collections[1]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[1]).not_to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()

    # click on the second step, nothing should happen because the form has not been validated yet
    step_items[1].locator('.stepper-head').click()
    expect(step_items[0]).to_have_attribute('aria-current', 'step')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')

    # click on the Next button should raise a form validation error
    expect(collections[0].locator('.dj-form-errors .dj-errorlist')).to_be_empty()
    fields_error_list = collections[0].locator('.dj-field-errors .dj-errorlist').all()
    assert len(fields_error_list) == 2
    expect(fields_error_list[0]).to_be_empty()
    expect(fields_error_list[1]).to_be_empty()
    spy = mocker.spy(FormCollectionView, 'patch')
    collections[0].locator('button[name="next"]').click()
    sleep(0.2)
    if viewname == 'empty_stepper_forced':
        # in forced submission mode, the form is submitted even if invalid
        spy.assert_called()
        assert spy.spy_return.status_code == 422
    else:
        spy.assert_not_called()
    expect(collections[0].locator('.dj-form-errors .dj-errorlist')).to_be_empty()
    expect(fields_error_list[0]).to_contain_text('This field is required.')
    expect(fields_error_list[1]).to_contain_text('This field is required.')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['empty_stepper'])
def test_steps_become_active(page, mocker, viewname):
    stepper_collection = page.locator('django-stepper-collection')
    step_items = stepper_collection.locator('ul.stepper-horizontal > li.stepper-step').all()
    collections = stepper_collection.locator('django-form-collection').all()

    collections[0].locator('input[name="first_name"]').fill("John")
    collections[0].locator('input[name="last_name"]').fill("Doe")
    spy = mocker.spy(FormCollectionView, 'patch')
    collections[0].locator('button[name="next"]').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200

    expect(step_items[0]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).to_have_attribute('aria-current', 'step')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')
    expect(collections[0]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[0]).not_to_be_visible()
    expect(collections[1]).to_have_attribute('aria-current', 'step')
    expect(collections[1]).to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()

    # fill the second step
    collections[1].locator('input[name="street"]').fill("123 Main St")
    collections[1].locator('input[name="postal_code"]').fill("12345")
    collections[1].locator('input[name="city"]').fill("Springfield")

    # return to the first step using the previous button
    collections[1].locator('button[name="previous"]').click()
    expect(step_items[0]).to_have_attribute('aria-current', 'step')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')
    expect(collections[0]).to_have_attribute('aria-current', 'step')
    expect(collections[0]).to_be_visible()
    expect(collections[1]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[1]).not_to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()
    expect(collections[0].locator('input[name="first_name"]')).to_have_value("John")
    expect(collections[0].locator('input[name="last_name"]')).to_have_value("Doe")

    # go back to the second step using the stepper
    step_items[1].locator('.stepper-head').click()
    expect(step_items[0]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).to_have_attribute('aria-current', 'step')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')
    expect(collections[0]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[0]).not_to_be_visible()
    expect(collections[1]).to_have_attribute('aria-current', 'step')
    expect(collections[1]).to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()
    expect(collections[1].locator('input[name="street"]')).to_have_value("123 Main St")
    expect(collections[1].locator('input[name="postal_code"]')).to_have_value("12345")
    expect(collections[1].locator('input[name="city"]')).to_have_value("Springfield")

    # go to the third step
    collections[1].locator('button[name="next"]').click()
    expect(step_items[0]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).to_have_attribute('aria-current', 'step')
    expect(step_items[2]).to_have_class('stepper-step visited')
    expect(collections[0]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[0]).not_to_be_visible()
    expect(collections[1]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[1]).not_to_be_visible()
    expect(collections[2]).to_have_attribute('aria-current', 'step')
    expect(collections[2]).to_be_visible()
    collections[2].locator('input[name="card_owner"]').fill("John Doe")
    collections[2].locator('input[name="card_number"]').fill("1234 5678 9012 3456")

    # submit the three form
    spy = mocker.spy(FormCollectionView, 'post')
    collections[2].locator('button[name="activate_submit"]').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {
        '_extra': {},
        'formset_data': {
            'contact': {'first_name': "John", 'last_name': "Doe"},
            'shipping': {'street': "123 Main St", 'postal_code': "12345", 'city': "Springfield"},
            'payment': {'card_owner': "John Doe", 'card_number': "1234 5678 9012 3456"},
        },
    }
    assert request_body == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['prefilled_stepper'])
def test_steps_already_visited(page, viewname):
    stepper_collection = page.locator('django-stepper-collection')
    step_items = stepper_collection.locator('ul.stepper-horizontal > li.stepper-step').all()
    collections = stepper_collection.locator('django-form-collection').all()
    expect(collections[0].locator('input[name="first_name"]')).to_have_value("John")
    expect(collections[0].locator('input[name="last_name"]')).to_have_value("Doe")
    expect(step_items[0]).to_have_attribute('aria-current', 'step')
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')
    expect(collections[0]).to_have_attribute('aria-current', 'step')
    expect(collections[0]).to_be_visible()
    expect(collections[1]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[1]).not_to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()

    # go to the second step using the stepper
    step_items[1].locator('.stepper-head').click()
    expect(step_items[0]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_attribute('aria-current', 'step')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[0]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[0]).not_to_be_visible()
    expect(collections[1]).to_have_attribute('aria-current', 'step')
    expect(collections[1]).to_be_visible()
    expect(collections[2]).not_to_have_attribute('aria-current', r'.*')
    expect(collections[2]).not_to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['prefilled_stepper'])
def test_steps_partially_valid_then_invalid(page, viewname):
    stepper_collection = page.locator('django-stepper-collection')
    step_items = stepper_collection.locator('ul.stepper-horizontal > li.stepper-step').all()
    collections = stepper_collection.locator('django-form-collection').all()
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).not_to_have_attribute('aria-current', r'.*')
    expect(step_items[2]).to_have_class('stepper-step')
    expect(collections[0]).to_have_attribute('aria-current', 'step')
    expect(collections[0]).to_be_visible()
    step_items[1].locator('.stepper-head').click()
    expect(collections[1]).to_be_visible()
    collections[1].locator('input[name="street"]').fill("123 Main St")
    collections[1].locator('input[name="postal_code"]').fill("12345")
    collections[1].locator('input[name="city"]').fill("Springfield")
    collections[1].locator('button[name="next"]').click()
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).to_have_class('stepper-step visited')
    expect(step_items[2]).to_have_class('stepper-step visited')
    expect(collections[2]).to_be_visible()

    # return to first step and make the first step invalid
    step_items[0].locator('.stepper-head').click()
    expect(collections[0]).to_be_visible()
    collections[0].locator('input[name="last_name"]').fill("")

    # then the second and third step should be inactive and impossible to reach
    step_items[1].locator('.stepper-head').click()
    expect(collections[1]).not_to_be_visible()
    expect(collections[0]).to_be_visible()
    expect(step_items[0]).to_have_class('stepper-step visited')
    expect(step_items[1]).to_have_class('stepper-step')
    expect(step_items[2]).to_have_class('stepper-step')
