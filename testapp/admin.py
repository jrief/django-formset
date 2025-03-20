from django.contrib import admin
from django.forms.models import ModelForm
from django.forms.widgets import RadioSelect

from formset.admin import ModelAdmin
# from formset.forms import ModelForm
from formset.widgets import DatePicker, Selectize, SelectizeMultiple, UploadedFileInput

from .forms.person import ModelPersonForm
from .models.person import PersonModel


class PersonModelForm(ModelForm):
    field_order = ['full_name', 'avatar', 'activity_days', 'activity_datetime']

    class Meta:
        model = PersonModel
        exclude = ['extra_data']
        widgets = {
            'avatar': UploadedFileInput,
            'gender': RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize(search_lookup='label__icontains'),
            'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
        }


@admin.register(PersonModel)
class PersonAdmin(ModelAdmin):
    save_as = True
    form = ModelPersonForm
    # form = PersonModelForm
