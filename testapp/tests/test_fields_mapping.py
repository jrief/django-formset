import pytest
from bs4 import BeautifulSoup, element
from django.forms.fields import ChoiceField
from django.forms.models import modelform_factory
from formset.templatetags.formsetify import _formsetify
from testapp.forms.product import ProductFormUnmapped
from testapp.models import ProductModel


class ProductFormMapped(ProductFormUnmapped):
    class Meta(ProductFormUnmapped.Meta):
        fields_map = {'properties': ['size'], 'extra_data': ['color']}


class PropertiesForm(ProductFormUnmapped):
    fit = ChoiceField(
        label="Fit",
        choices=[
            ('R', "Regular"),
            ('S', "Slim"),
            ('L', "Loose"),
        ],
    )

    class Meta:
        model = ProductModel
        fields_map = {'properties': ['size', 'color'], 'extra_data': ['fit']}



def test_render_unmapped_form():
    form = ProductFormUnmapped()
    assert form._meta.fields is None
    assert form._meta.exclude is None
    with pytest.raises(AttributeError):
        form._meta.fields_map
    html = _formsetify(form).render(template_name='formset/default/form.html')
    soup = BeautifulSoup(html, 'html.parser')
    form_element = soup.find('form', id='id_productformunmapped')
    assert isinstance(form_element, element.Tag)
    title_element = form_element.find_next('input', id='id_title')
    assert isinstance(title_element, element.Tag)
    price_element = title_element.find_next('input', id='id_price')
    assert isinstance(price_element, element.Tag)
    properties_field = price_element.find_next('textarea', attrs={'name': 'properties'})
    assert isinstance(properties_field, element.Tag)
    extra_data_field = properties_field.find_next('textarea', attrs={'name': 'extra_data'})
    assert isinstance(extra_data_field, element.Tag)
    size_fields = extra_data_field.find_all_next('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = size_fields[3].find_next('input', id='id_color', attrs={'name': 'color', 'type': 'color'})
    assert isinstance(color_field, element.Tag)


def test_render_mapped_form():
    form = ProductFormMapped()
    expected = ['title', 'price', 'properties', 'size', 'extra_data', 'color', 'supplier_name']
    assert form._meta.fields == expected
    assert form._meta.exclude is None
    assert form._meta.fields_map == {'properties': ['size'], 'extra_data': ['color']}
    html = _formsetify(form).render(template_name='formset/default/form.html')
    soup = BeautifulSoup(html, 'html.parser')
    form_element = soup.find('form', id='id_productformmapped')
    assert isinstance(form_element, element.Tag)
    title_element = form_element.find_next('input', id='id_title')
    assert isinstance(title_element, element.Tag)
    price_element = title_element.find_next('input', id='id_price')
    assert isinstance(price_element, element.Tag)
    assert price_element.find_next('textarea', attrs={'name': 'properties'}) is None
    assert price_element.find_next('textarea', attrs={'name': 'extra_data'}) is None
    size_fields = price_element.find_all_next('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = size_fields[3].find_next('input', id='id_color', attrs={'name': 'color', 'type': 'color'})
    assert isinstance(color_field, element.Tag)


@pytest.mark.django_db
def test_submit_mapped_form():
    request_data = {
        'title': 'Test Product',
        'price': '100.00',
        'size': 'XL',
        'color': '#ff0000',
    }
    form = ProductFormMapped(data=request_data)
    assert form.is_valid() is True
    product = form.save()
    assert product.title == request_data['title']
    assert product.price == float(request_data['price'])
    assert product.properties == {'size': request_data['size']}
    assert product.extra_data == {'color': request_data['color']}


def test_render_factorized_form():
    ProductForm = modelform_factory(ProductModel, form=ProductFormMapped, fields=['title'])
    form = ProductForm()
    assert form._meta.fields == ['title']
    assert form._meta.exclude is None
    assert form._meta.fields_map == {'properties': ['size'], 'extra_data': ['color']}
    html = _formsetify(form).render(template_name='formset/default/form.html')
    soup = BeautifulSoup(html, 'html.parser')
    form_element = soup.find('form', id='id_productmodelform')
    assert isinstance(form_element, element.Tag)
    title_element = form_element.find_next('input', id='id_title')
    assert isinstance(title_element, element.Tag)
    assert title_element.find_next('input', id='id_price') is None
    assert title_element.find_next('textarea', attrs={'name': 'properties'}) is None
    assert title_element.find_next('textarea', attrs={'name': 'extra_data'}) is None
    size_fields = title_element.find_all_next('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = size_fields[3].find_next('input', id='id_color', attrs={'name': 'color', 'type': 'color'})
    assert isinstance(color_field, element.Tag)


def test_render_factorized_properties_form():
    ProductForm = modelform_factory(ProductModel, form=PropertiesForm, fields='__all__')
    form = ProductForm()
    expected = ['title', 'price', 'properties', 'size', 'color', 'extra_data', 'fit', 'supplier_name']
    assert form._meta.fields == expected
    assert form._meta.exclude is None
    assert form._meta.fields_map == {'properties': ['size', 'color'], 'extra_data': ['fit']}
    html = _formsetify(form).render(template_name='formset/default/form.html')
    soup = BeautifulSoup(html, 'html.parser')
    form_element = soup.find('form', id='id_productmodelform')
    assert isinstance(form_element, element.Tag)
    title_element = form_element.find_next('input', id='id_title')
    assert isinstance(title_element, element.Tag)
    price_element = title_element.find_next('input', id='id_price')
    assert isinstance(price_element, element.Tag)
    assert price_element.find_next('textarea', attrs={'name': 'properties'}) is None
    assert price_element.find_next('textarea', attrs={'name': 'extra_data'}) is None
    size_fields = price_element.find_all_next('input', attrs={'name': 'size', 'type': 'radio'})
    assert len(size_fields) == 4
    color_field = size_fields[3].find_next('input', id='id_color', attrs={'name': 'color', 'type': 'color'})
    assert isinstance(color_field, element.Tag)
    fit_field = color_field.find_next('select', id='id_fit', attrs={'name': 'fit'})
    assert isinstance(fit_field, element.Tag)
