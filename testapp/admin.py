from django.contrib import admin
from django.forms.widgets import RadioSelect

from formset.admin import ModelAdmin
from formset.calendar import CalendarResponseMixin
from formset.views import IncompleteSelectResponseMixin
from formset.widgets import DatePicker, DualSelector, Selectize, SelectizeMultiple

from .models.person import PersonModel


@admin.register(PersonModel)
class PersonAdmin(CalendarResponseMixin, IncompleteSelectResponseMixin, ModelAdmin):
    save_as = True

    def get_form(self, request, obj=None, change=False, **kwargs):
        kwargs['widgets'] = {
            'gender': RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize,
            #'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
            'opinions': DualSelector(search_lookup='label__icontains'),
        }
        form = super().get_form(request, obj, change, **kwargs)
        return form
