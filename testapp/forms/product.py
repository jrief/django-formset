from django.forms.fields import CharField, RegexField, ChoiceField
from django.forms.widgets import RadioSelect, TextInput
from formset.fieldset import Fieldset
from formset.forms import ModelForm
from formset.widgets import CountrySelectize
from django_countries import countries

from testapp.models import ProductModel


class ProductFormUnmapped(ModelForm):
    size = ChoiceField(
        label="Size",
        choices=[
            ('S', "Small"),
            ('M', "Medium"),
            ('L', "Large"),
            ('XL', "Extra Large"),
        ],
        widget=RadioSelect,
    )
    color = RegexField(
        regex=r'^#[a-zA-Z0-9]{6}$',
        label="Color",
        widget=TextInput(attrs={'type': 'color'}),
    )

    class Meta:
        model = ProductModel
        fields = '__all__'


class Supplier(Fieldset):
    legend = "Supplier"

    name = CharField(
        label="Name",
        max_length=100,
        required=False,
    )
    origin = ChoiceField(
        label="Country of Origin",
        widget=CountrySelectize,
        choices=countries,
    )


class ProductForm(ProductFormUnmapped):
    """
    How to map fields for a Django Form and a Fieldset to one or more JSONField-s.
    """
    supplier = Supplier()

    class Meta(ProductFormUnmapped.Meta):
        fields = ['title', 'price', 'properties', 'supplier_name']
        # exclude = ['extra_data']
        fields_map = {
            'properties': ['size', 'color', 'supplier.origin'],
            'supplier_name': 'supplier.name',
        }
