from django.contrib import admin

from .models import PayloadModel
from .forms.complete import CompleteForm


# @admin.register(DummyModel)
class DummyAdmin(admin.ModelAdmin):
    form = CompleteForm
    change_form_template = 'admin/formset/change_form.html'
