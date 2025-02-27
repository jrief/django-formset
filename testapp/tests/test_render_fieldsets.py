import json

from bs4 import BeautifulSoup
from django.forms import fields, forms

from formset.fieldset import Fieldset
from formset.form import Form
from formset.views import FormView


class AddressFieldset(Fieldset):
    recipient = fields.CharField(label="Recipient")
    postal_code = fields.CharField(label="Postal Code")
    city = fields.CharField(label="City")


class CustomerForm(Form):
    billing_address = AddressFieldset(legend="Billing Address")
    shipping_address = AddressFieldset(legend="Shipping Address")
    use_billing_address = fields.BooleanField(label="Use Billing Address for Shipping", required=False)


def test_render_fieldsets(rf):
    view = FormView.as_view(
        form_class=CustomerForm,
        template_name='testapp/native-form.html',
        success_url='/success',
    )
    response = view(rf.get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    form_wrapper = soup.find('div', class_='dj-form')
    assert form_wrapper is not None
    fieldsets = form_wrapper.find_all('fieldset')
    assert len(fieldsets) == 2
    assert fieldsets[0].attrs['name'] == 'billing_address'
    assert fieldsets[0].legend.string == "Billing Address"
    assert fieldsets[1].attrs['name'] == 'shipping_address'
    assert fieldsets[1].legend.string == "Shipping Address"
    for fieldset in fieldsets:
        fieldset_name = fieldset.attrs['name']
        input_fields = fieldset.find_all('input')
        assert len(input_fields) == 3
        assert input_fields[0].attrs['id'] == f'id_{fieldset_name}.recipient'
        assert input_fields[0].attrs['name'] == f'{fieldset_name}.recipient'
        assert input_fields[1].attrs['id'] == f'id_{fieldset_name}.postal_code'
        assert input_fields[1].attrs['name'] == f'{fieldset_name}.postal_code'
        assert input_fields[2].attrs['id'] == f'id_{fieldset_name}.city'
        assert input_fields[2].attrs['name'] == f'{fieldset_name}.city'
    checkbox_input = form_wrapper.find('input', type='checkbox')
    assert checkbox_input is not None
    assert checkbox_input.attrs['name'] == 'use_billing_address'


def test_submit_fieldsets(rf):
    view = FormView.as_view(
        form_class=CustomerForm,
        template_name='testapp/native-form.html',
        success_url='/success',
    )
    form_data = {
        "formset_data": {
            "billing_address.recipient": "John Doe",
            "billing_address.postal_code": "12345",
            "billing_address.city": "Springfield",
            "shipping_address.recipient": "Jane Doe",
            "shipping_address.postal_code": "54321",
            "shipping_address.city": "Shelbyville",
            "use_billing_address": "on",
        }
    }
    response = view(rf.post('/', form_data, content_type='application/json'))
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
