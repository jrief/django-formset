from django.contrib import admin
from django.forms.fields import DateTimeField, IntegerField
from django.forms.forms import Form
from django.forms.widgets import RadioSelect
from django.forms.models import BaseModelForm, ModelForm, modelform_factory

from formset.admin import ModelAdmin
from formset.widgets import DatePicker, DateTimePicker, DualSelector, Selectize, SelectizeMultiple

from .models.person import PersonModel


class PersonFormBase(ModelForm):
    # field_order = ['full_name', 'avatar', 'activity_datetime', 'activity_days']
    activity_datetime = DateTimeField(
        label="Activity timestamp",
        widget=DateTimePicker,
    )
    activity_days = IntegerField(
        label="Activity days",
    )

    class Meta:
        fields_map = {'extra_data': ['activity_datetime', 'activity_days']}


class PersonForm(PersonFormBase, ModelForm):
    class Meta:
        model = PersonModel
        # fields = '__all__'
        # fields = ['full_name', 'avatar', 'gender', 'birth_date', 'extra_data', 'continent', 'opinion', 'opinions']
        exclude = ['is_active']
        widgets = {
            'gender': RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize(search_lookup='label__icontains'),
            #'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
            'opinions': DualSelector(search_lookup='label__icontains'),
        }
        fields_map = {'extra_data': ['activity_datetime', 'activity_days']}
        disabled_fields = ['continent', 'activity_days']


@admin.register(PersonModel)
class PersonAdmin(ModelAdmin):
    save_as = True
    # form = PersonForm
    form = modelform_factory(
        PersonModel,
        form=PersonFormBase,
        exclude=['is_active'],
        widgets = {
            'gender': RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize(search_lookup='label__icontains'),
            #'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
            'opinions': DualSelector(search_lookup='label__icontains'),
        }
    )
