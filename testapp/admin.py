from django.contrib import admin

from formset.admin import ModelAdmin

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
    form = ModelPersonForm


@admin.register(ProductModel)
class ProductAdmin(ModelAdmin):
    save_as = True
    form = ProductForm
