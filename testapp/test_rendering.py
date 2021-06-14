import pytest

from bs4 import BeautifulSoup

from django.forms.widgets import Textarea
from django.test import RequestFactory

from .forms import DefaultMixinForm, SubscribeForm, BootstrapMixinForm, BulmaMixinForm, \
                   FoundationMixinForm, TailwindMixinForm
from .views import SubscribeFormView, sample_subscribe_data

http_request = RequestFactory().get('/')


@pytest.fixture(params=[
    ('default/formsetify.html', SubscribeForm),
    ('default/formsetify.html', SubscribeForm, sample_subscribe_data),
    ('default/render_groups.html', SubscribeForm),
    ('default/render_groups.html', SubscribeForm, sample_subscribe_data),
    ('default/mixin_form.html', DefaultMixinForm),
    ('default/mixin_form.html', DefaultMixinForm, sample_subscribe_data),
    ('bootstrap/formsetify.html', SubscribeForm),
    ('bootstrap/render_groups.html', SubscribeForm),
    ('bootstrap/mixin_form.html', BootstrapMixinForm),
    ('bulma/formsetify.html', SubscribeForm),
    ('bulma/render_groups.html', SubscribeForm),
    ('bulma/mixin_form.html', BulmaMixinForm),
    ('foundation/formsetify.html', SubscribeForm),
    ('foundation/render_groups.html', SubscribeForm),
    ('foundation/mixin_form.html', FoundationMixinForm),
    ('tailwind/formsetify.html', SubscribeForm),
    ('tailwind/render_groups.html', SubscribeForm),
    ('tailwind/mixin_form.html', TailwindMixinForm),
], scope='session')
def view(request):
    view_initkwargs = {
        'template_name': request.param[0],
        'form_class': request.param[1],
    }
    if len(request.param) == 3:
        view_initkwargs['initial'] = request.param[2]
    return SubscribeFormView.as_view(**view_initkwargs)


@pytest.fixture(scope='session')
def form_soup(view):
    response = view(http_request)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    form = view.view_initkwargs['form_class']()
    initial = view.view_initkwargs['initial'] if 'initial' in view.view_initkwargs else {}
    framework = view.view_initkwargs['template_name'].split('/')[0]
    return form, soup, initial, framework


@pytest.mark.parametrize('field_name', SubscribeForm.base_fields.keys())
def test_default_fields(form_soup, field_name):
    form_name = form_soup[0].name
    bf = form_soup[0][field_name]
    soup = form_soup[1]
    initial_value = form_soup[2].get(field_name)
    framework = form_soup[3]
    field_elem = soup.find(id=f'subscribe_id_{field_name}')
    assert field_elem is not None
    widget_type = 'textarea' if isinstance(bf.field.widget, Textarea) else bf.field.widget.input_type
    allow_multiple_selected = getattr(bf.field.widget, 'allow_multiple_selected', False)
    if widget_type in ['text', 'email', 'date', 'number', 'password', 'textarea']:
        if bf.field.required:
            assert 'required' in field_elem.attrs
    if widget_type in ['text', 'email', 'number']:
        if initial_value:
            assert field_elem.attrs['value'] == str(initial_value)
    if widget_type in ['text', 'email', 'password']:
        min_length = getattr(bf.field, 'min_length', None)
        if min_length:
            assert field_elem.attrs['minlength'] == str(min_length)
        max_length = getattr(bf.field, 'max_length', None)
        if max_length:
            assert field_elem.attrs['maxlength'] == str(max_length)
    if widget_type in ['date']:
        if initial_value:
            assert field_elem.attrs['value'] == initial_value.strftime('%Y-%m-%d')
    if widget_type == 'checkbox' and not allow_multiple_selected:
        input_elems = [field_elem]
        if initial_value:
            assert 'checked' in field_elem.attrs
    if widget_type == 'radio' or widget_type == 'checkbox' and allow_multiple_selected:
        input_elems = field_elem.find_all('input', type=widget_type)
        assert len(input_elems) > 0
        if widget_type == 'radio':
            if bf.field.required:
                assert all('required' in el.attrs for el in input_elems)
        if initial_value:
            if not allow_multiple_selected:
                initial_value = [initial_value]
            assert all('checked' in el.attrs for el in input_elems if el.attrs['value'] in initial_value)
            assert not any('checked' in el.attrs for el in input_elems if el.attrs['value'] not in initial_value)
    if widget_type == 'select':
        if bf.field.required:
            assert 'required' in field_elem.attrs
        opt_elems = field_elem.find_all('option')
        assert len(opt_elems) > 0
        if initial_value:
            if not allow_multiple_selected:
                initial_value = [initial_value]
            assert all('selected' in el.attrs for el in opt_elems if el.attrs['value'] in initial_value)
            assert not any('selected' in el.attrs for el in opt_elems if el.attrs['value'] not in initial_value)
    if widget_type == 'textarea':
        if bf.field.required:
            assert 'required' in field_elem.attrs
        if initial_value:
            field_elem.text.strip() == initial_value

    if bf.field.widget.is_hidden:
        formset = field_elem.find_parent('django-formset')
        assert formset is not None
        assert len(formset.attrs.get('endpoint', '')) > 0
        form_elem = formset.find('form')
        assert form_elem.attrs['name'] == form_name
        errors_elem = form_elem.find('div', class_='dj-form-errors')
        assert errors_elem is not None
        errorlist_elem = errors_elem.find('ul', class_='dj-errorlist')
        assert errorlist_elem is not None
        placeholder_elem = errorlist_elem.find('li', class_='dj-placeholder')
        assert placeholder_elem is not None
        return

    field_group = field_elem.find_parent('django-field-group')
    assert field_group is not None
    if bf.field.required:
        if allow_multiple_selected and widget_type == 'checkbox':
            assert 'dj-required-any' in field_group.attrs['class']
        else:
            assert 'dj-required' in field_group.attrs['class']
    errorlist_elem = field_group.find('ul', class_='dj-errorlist')
    assert errorlist_elem is not None
    placeholder_elem = errorlist_elem.find('li', class_='dj-placeholder')
    assert placeholder_elem is not None

    if bf.field.help_text:
        help_text = None
        if framework == 'default':
            help_text = field_group.find('span', class_='dj-help-text')
        elif framework == 'bootstrap':
            help_text = field_group.find('span', class_='form-text text-muted')
        elif framework == 'tailwind':
            help_text = field_group.find('p', class_='formset-help-text')
        assert not help_text or help_text.text == bf.field.help_text


    if bf.field.label:
        label = field_group.find('label')
        assert bf.label == label.text.rstrip(':')
        if allow_multiple_selected and widget_type == 'checkbox':
            assert 'for' not in label.attrs
            labels = field_elem.find_all('label')
            assert len(bf.subwidgets) == len(labels)
            for subwidget, sublabel in zip(bf.subwidgets, labels):
                assert subwidget.id_for_label == sublabel.attrs['for']
        else:
            assert label.attrs['for'] == bf.id_for_label
        if framework == 'tailwind':
            if widget_type != 'checkbox' or allow_multiple_selected:
                assert 'formset-label' in label.attrs['class']

    if framework == 'bootstrap':
        assert 'form-group' in field_group.attrs['class']
        if widget_type in ['text', 'email', 'number', 'date', 'select', 'textarea', 'password']:
            assert 'form-control' in field_elem.attrs['class']
        elif widget_type in ['checkbox', 'radio']:
            for input_elem in input_elems:
                assert 'form-check-input' in input_elem.attrs['class']

    if framework == 'tailwind':
        if widget_type == 'text':
            assert 'formset-text-input' in field_elem.attrs['class']
        if widget_type == 'number':
            assert 'formset-number-input' in field_elem.attrs['class']
        elif widget_type == 'email':
            assert 'formset-email-input' in field_elem.attrs['class']
        elif widget_type == 'date':
            assert 'formset-date-input' in field_elem.attrs['class']
        elif widget_type == 'select':
            if allow_multiple_selected:
                assert 'formset-select-multiple' in field_elem.attrs['class']
            else:
                assert 'formset-select' in field_elem.attrs['class']
        elif widget_type == 'textarea':
            assert 'formset-textarea' in field_elem.attrs['class']
        elif widget_type == 'password':
            assert 'formset-password-input' in field_elem.attrs['class']
        elif widget_type == 'checkbox':
            if allow_multiple_selected:
                for input_elem in input_elems:
                    assert 'formset-checkbox-multiple' in input_elem.attrs['class']
            else:
                assert 'formset-checkbox' in input_elems[0].attrs['class']
        elif widget_type == 'radio':
            for input_elem in input_elems:
                assert 'formset-radio-select' in input_elem.attrs['class']

    # CSS framework "Bulma" and "Foundation 6" do not add special classes to their field-groups
