import json
import pytest
from time import sleep
from playwright.sync_api import expect

from django.urls import path
from django.forms import fields, forms

from formset.collection import FormCollection
from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.views import FormCollectionView
from formset.widgets import Button


class CustomerForm(forms.Form):
    name = fields.CharField()
    click_inside = Activator()


class PopupForm(DialogForm):
    title = "Edit Name"
    induce_open = 'customer.click_inside:active || click_outside:active || customer.name == "OpenSesame"'
    induce_close = '.close:active || .submit:active'

    name = fields.CharField()
    close = Activator(
        label="Close",
        widget=Button(
            action='cancel',
        ),
    )
    submit = Activator(
        label="Apply",
        widget=Button(
            action='apply',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )


class DialogCollection(FormCollection):
    customer = CustomerForm()
    popup = PopupForm()
    click_outside = Activator()


class DemoFormCollectionView(FormCollectionView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('dialog', DemoFormCollectionView.as_view(
        collection_class=DialogCollection,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='dialog'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['dialog'])
def test_submit_dialog(page, mocker, viewname):
    # check that induce_open = 'customer.click_inside:active || …' works
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(1).locator('> dialog')
    expect(dialog).not_to_be_visible()
    form_collection.first.locator('button[name="click_inside"]').click()
    expect(dialog).to_be_visible()
    dialog.locator('button[name="submit"]').click()
    popup_name_input = dialog.locator('input[name="name"]')
    expect(popup_name_input.locator('+ [role="alert"]')).to_have_text("This field is required.")
    expect(dialog).to_be_visible()
    expect(dialog.locator('> div.dialog-header > h3')).to_have_text("Edit Name")
    popup_name_input.fill("Barbara")
    expect(popup_name_input.locator('+ [role="alert"]')).to_be_empty()
    popup_name_input.blur()
    dialog.locator('button[name="submit"]').click()
    expect(dialog).not_to_be_visible()
    customer_name_input = form_collection.first.locator('input[name="name"]')
    customer_name_input.fill("Liskov")
    customer_name_input.blur()
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('button[df-click="submit -> proceed"]').click()
    sleep(0.25)
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['customer']['name'] == "Liskov"
    assert request['formset_data']['popup']['name'] == "Barbara"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['dialog'])
def test_open_dialog(page, viewname):
    # check that induce_open = '… || customer.name == "OpenSesame"' works
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(1).locator('> dialog')
    expect(dialog).not_to_be_visible()
    customer_name_input = form_collection.first.locator('input[name="name"]')
    customer_name_input.fill("Open")
    customer_name_input.blur()
    expect(dialog).not_to_be_visible()
    customer_name_input.fill("OpenSesame")
    customer_name_input.blur()
    expect(dialog).to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['dialog'])
def test_close_dialog(page, viewname):
    # check that induce_open = '… || click_outside:active || …' works
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(1).locator('> dialog')
    expect(dialog).not_to_be_visible()
    form_collection.nth(2).locator('button[name="click_outside"]').click()
    expect(dialog).to_be_visible()
    dialog.locator('input[name="name"]').blur()
    dialog.locator('button[name="close"]').click()
    expect(dialog).not_to_be_visible()
