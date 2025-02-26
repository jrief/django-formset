from django.contrib import admin
from formset.admin import ModelAdmin

from .models.person import PersonModel


@admin.register(PersonModel)
class PersonAdmin(ModelAdmin):
    pass
