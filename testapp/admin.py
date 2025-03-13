from django.contrib import admin
from django.forms.widgets import RadioSelect

from formset.admin import ModelAdmin
from formset.widgets import DatePicker, DualSelector, Selectize, SelectizeMultiple

from .models.person import PersonModel


@admin.register(PersonModel)
class PersonAdmin(ModelAdmin):
    save_as = True

    def get_form(self, request, obj=None, change=False, **kwargs):
        kwargs['widgets'] = {
            'gender': RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize(search_lookup='label__icontains'),
            #'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
            'opinions': DualSelector(search_lookup='label__icontains'),
        }
        form = super().get_form(request, obj, change, **kwargs)
        return form
