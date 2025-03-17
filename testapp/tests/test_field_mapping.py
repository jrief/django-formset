import pytest
from bs4 import BeautifulSoup

from django.forms.models import modelform_factory
from django.views.generic.edit import CreateView, UpdateView

from formset.templatetags.formsetify import _formsetify
from formset.views import FormViewMixin

from testapp.forms.product import ProductForm
from testapp.models import ProductModel


class CreateView(FormViewMixin, CreateView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


def test_create_form_class():
    form = ProductForm()
    assert form._meta.fields is None
    assert form._meta.exclude is None
    with pytest.raises(AttributeError):
        form._meta.fields_map
    html = _formsetify(form).render(template_name='formset/form.html')
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.find('form', id='id_productform')
    properties_field = soup.find('textarea', attrs={'name': 'properties'})
    assert properties_field is not None
    extra_data_field = soup.find('textarea', attrs={'name': 'extra_data'})
    assert extra_data_field is not None
    size_fields = soup.find_all('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = soup.find('input', attrs={'name': 'color', 'type': 'color'})
    assert color_field is not None


def test_render_empty_form(rf):
    view = CreateView.as_view(form_class=ProductForm)
    response = view(rf.get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    django_formset = soup.find('django-formset')
    assert django_formset is not None
    properties_field = django_formset.find('textarea', attrs={'name': 'properties'})
    assert properties_field is not None
    extra_data_field = django_formset.find('textarea', attrs={'name': 'extra_data'})
    assert extra_data_field is not None
    size_fields = django_formset.find_all('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = django_formset.find('input', attrs={'name': 'color', 'type': 'color'})
    assert color_field is not None
