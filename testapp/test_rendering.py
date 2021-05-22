import pytest

from bs4 import BeautifulSoup

from django.forms.widgets import Textarea

from .forms import DefaultMixinForm, SubscribeForm
from .views import SubscribeFormView


class DefaultSubscribeForm(DefaultMixinForm, SubscribeForm):
    pass


# views = [
#     SubscribeFormView.as_view(
#         template_name='default/formsetify.html',
#         form_class=SubscribeForm,
#     ),
#     SubscribeFormView.as_view(
#         template_name='default/render_groups.html',
#         form_class=SubscribeForm,
#     ),
#     SubscribeFormView.as_view(
#         template_name='default/mixin_form.html',
#         form_class=DefaultSubscribeForm,
#     ),
# ]


@pytest.fixture(params=[
    ('default/formsetify.html', SubscribeForm),
    ('default/render_groups.html', SubscribeForm),
    ('default/mixin_form.html', DefaultSubscribeForm),
])
def view(request):
    return SubscribeFormView.as_view(
        template_name=request.param[0],
        form_class=request.param[1],
    )


@pytest.fixture(scope='function')
def form_soup(rf, view):
    response = view(rf.get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    form = view.view_initkwargs['form_class']()
    return form, soup


@pytest.mark.parametrize('field_name', SubscribeForm.base_fields.keys())
def test_fields(form_soup, field_name):
    form, soup = form_soup
    bf = form[field_name]
    field_elem = soup.find(id=f'id_{field_name}')
    assert field_elem is not None
    input_type = 'textarea' if isinstance(bf.field.widget, Textarea) else bf.field.widget.input_type
    allow_multiple_selected = getattr(bf.field.widget, 'allow_multiple_selected', False)
    if input_type in ['text', 'email', 'date', 'number', 'textarea']:
        if bf.field.required:
            assert 'required' in field_elem.attrs
    if input_type in ['text', 'email', 'number', 'textarea']:
        if bf.field.initial:
            assert field_elem.attrs['value'] == str(bf.field.initial)
    if input_type in ['text', 'email']:
        min_length = getattr(bf.field, 'min_length', None)
        if min_length:
            assert field_elem.attrs['minlength'] == str(min_length)
        max_length = getattr(bf.field, 'max_length', None)
        if max_length:
            assert field_elem.attrs['maxlength'] == str(max_length)
    if input_type == 'radio':
        input_elems = field_elem.find_all('input')
        assert len(input_elems) > 0
        if bf.field.required:
            assert all('required' in el.attrs for el in input_elems)

    field_group = field_elem.find_parent('django-field-group')
    if bf.field.widget.is_hidden:
        assert field_group is None
    else:
        assert field_group is not None
        if bf.field.required:
            assert {'dj-required', 'dj-required-any'}.intersection(field_group.attrs['class'])
        errorlist_elem = field_group.find('ul', class_='dj-errorlist')
        assert errorlist_elem is not None
        placeholder_elem = errorlist_elem.find('li', class_='dj-placeholder')
        assert placeholder_elem is not None

    if bf.field.help_text:
        help_text = field_group.find('span', class_='dj-help-text')
        assert help_text is not None

