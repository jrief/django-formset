from django.forms.fields import RegexField, ChoiceField
from django.forms.widgets import RadioSelect, TextInput
from formset.forms import ModelForm

from testapp.models import ProductModel


class ProductForm(ModelForm):
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
        # exclude = ['extra_data']
        fields_map = {'properties': ['size'], 'extra_data': ['color']}
