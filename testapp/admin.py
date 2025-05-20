from django.contrib import admin
from django.forms.models import ModelForm
from django.forms.widgets import RadioSelect

from formset.admin import ModelAdmin
from formset.widgets import DatePicker, Selectize, SelectizeMultiple, UploadedFileInput

from .forms.company import CompanyCollection
from .forms.person import ModelPersonForm
from .forms.product import ProductForm
from .models.company import Company
from .models.person import PersonModel
from .models.product import ProductModel


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    save_as = True
    collection_class = CompanyCollection


@admin.register(PersonModel)
class PersonAdmin(ModelAdmin):
    save_as = True
    form = ModelPersonForm


@admin.register(ProductModel)
class ProductAdmin(ModelAdmin):
    save_as = True
    form = ProductForm
