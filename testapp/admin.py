from django.contrib import admin

from .models import DummyModel
from .forms import SubscribeForm


@admin.register(DummyModel)
class DummyAdmin(admin.ModelAdmin):
    form = SubscribeForm
    change_form_template = 'admin/formset/change_form.html'
