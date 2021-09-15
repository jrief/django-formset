import pytest

from django.forms import Form, models
from django.urls import path

from formset.views import FormView
from formset.widgets import Selectize

from testapp.models import ChoicesModel


test_fields = dict(
    tenant=models.ModelChoiceField(
        label="Choose Tenant",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
    ),
    tenant_required = models.ModelChoiceField(
        label="Choose Tenant",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
    ),
    tenant_initialized=models.ModelChoiceField(
        label="Choose Tenant",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
    ),
    tenant_required_initialized=models.ModelChoiceField(
        label="Choose Tenant",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
    ),
)

views = {
    f'selectize{ctr}': FormView.as_view(
        template_name='tests/form_with_button.html',
        form_class=type(f'{tpl[0]}_form', (Form,), {'name': tpl[0], 'model_field': tpl[1]}),
        success_url='/success',
    )
    for ctr, tpl in enumerate(test_fields.items())
}

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.fixture
def view(viewname):
    return views[viewname]


@pytest.fixture
def form(view):
    return view.view_initkwargs['form_class']()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_form_validated(page, form):
    assert page.query_selector('django-formset form') is not None
    if 'required' in form.name:
        assert page.query_selector('django-formset form:valid') is None
        assert page.query_selector('django-formset form:invalid') is not None
    else:
        assert page.query_selector('django-formset form:valid') is not None
        assert page.query_selector('django-formset form:invalid') is None
