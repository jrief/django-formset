from collections import namedtuple
import pytest
import json

from django.forms import fields, Form, widgets
from django.urls import path

from formset.views import FormsetView


FieldTuple = namedtuple('FieldTuple', ['name', 'field', 'extra_context'])


def snake2camel(string):
    return ''.join(s.capitalize() for s in string.split('_'))


test_fields = dict(
    empty_valid=fields.CharField(
        required=False,
    ),
    empty_invalid=fields.CharField(
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
    ),
    prefilled_valid=fields.CharField(
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
        initial='ABC',
    ),
    prefilled_invalid=fields.CharField(
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
        initial='A',
    ),
    regex_valid=fields.RegexField(
        r'^[A-Z]+$',
        initial='A',
        error_messages={'invalid': "All letters must be in upper case."},
    ),
    regex_invalid=fields.RegexField(
        r'^[A-Z]+$',
        initial='a',
        error_messages={'invalid': "All letters must be in upper case."},
    ),
)

views = {
    f'form{ctr}': FormsetView.as_view(
        template_name='form.html',
        form_class=type(snake2camel(f'{tpl.name}_form'), (Form,), {'name': tpl.name, 'something': tpl.field}),
        success_url='/success',
        extra_context=tpl.extra_context,
    )
    for ctr, tpl in enumerate(FieldTuple(name, field, {'force_submission': fs, 'withhold_messages': wm})
        for name, field in test_fields.items()
        for fs in [False, True]
        for wm in [False, True]
    )
}

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.fixture
def view(viewname):
    return views[viewname]


@pytest.fixture
def form(view):
    return view.view_initkwargs['form_class']()


@pytest.fixture
def bound_form(view):
    form_class = view.view_initkwargs['form_class']
    data = {name: field.initial for name, field in form_class.base_fields.items() if field.initial}
    return form_class(data)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_form_validity(page, bound_form):
    form_elem_valid = page.query_selector('django-formset form:valid')
    form_elem_invalid = page.query_selector('django-formset form:invalid')
    if bound_form.is_valid():
        assert form_elem_valid is not None
        assert form_elem_invalid is None
    else:
        assert form_elem_valid is None
        assert form_elem_invalid is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_touch_input_field(page, form):
    field_group = page.query_selector('django-formset django-field-group')
    assert 'dj-untouched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-touched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')
    placeholder = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder')
    assert placeholder.inner_text() == ''
    name = next(iter(form.fields.keys()))
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    assert 'dj-touched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-untouched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_touch_and_blur_input_field(page, view, form):
    name = next(iter(form.fields.keys()))
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    input_elem.evaluate('elem => elem.blur()')
    input_elem_valid = page.query_selector(f'django-formset form input[name="{name}"]:valid')
    input_elem_invalid = page.query_selector(f'django-formset form input[name="{name}"]:invalid')
    withhold_messages = view.view_initkwargs['extra_context']['withhold_messages']
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    if form.name in ['empty_valid', 'prefilled_valid', 'regex_valid', 'email_valid']:
        assert placeholder_text == ''
        assert input_elem_valid is not None
        assert input_elem_invalid is None
    elif form.name == 'empty_invalid':
        assert placeholder_text == "" if withhold_messages else "This field is required."
        assert input_elem_valid is None
        assert input_elem_invalid is not None
    elif form.name == 'prefilled_invalid':
        assert placeholder_text == "" if withhold_messages else "Ensure this value has at least 2 characters."
        assert input_elem_valid is None
        assert input_elem_invalid is not None
    elif form.name == 'regex_invalid':
        assert placeholder_text == "" if withhold_messages else "All letters must be in upper case."
        assert input_elem_valid is None
        assert input_elem_invalid is not None
    elif form.name == 'email_invalid':
        assert placeholder_text == "" if withhold_messages else "Enter a valid email address."
        assert input_elem_valid is None
        assert input_elem_invalid is not None
    else:
        pytest.fail(f"Unknown form class: {form}")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_touch_and_change_input_field(page, form):
    name = next(iter(form.fields.keys()))
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    page.keyboard.press('Backspace')
    input_elem.type("XYZ")
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector('django-formset form:valid') is not None
    assert page.query_selector('django-formset form:invalid') is None
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is not None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_valid_form_submission(page, mocker, view, form):
    field_name = next(iter(form.fields.keys()))
    input_elem = page.query_selector(f'django-formset form input[name="{field_name}"]')
    input_elem.click()
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    input_elem.type("XYZ")
    input_elem.evaluate('elem => elem.blur()')
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request[form.name][field_name] == "XYZ"
    assert spy.spy_return.status_code == 200
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == view.view_initkwargs['success_url']
    assert page.query_selector('django-formset .dj-errorlist > .dj-placeholder').inner_text() == ''


urlpatterns.append(
    path('email_form', FormsetView.as_view(
        template_name='form.html',
        form_class=type('EmailForm', (Form,), {'name': 'email_form', 'email': fields.EmailField(initial="john@doe")}),
        success_url='/success',
    ), name='email_form')
)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['email_form'])
def test_email_field(page):
    name = 'email'
    assert page.query_selector('django-formset form:valid') is not None
    assert page.query_selector('django-formset form:invalid') is None
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is not None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is None
    input_elem.click()
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is not None
    assert page.query_selector('django-formset form:valid') is None
    assert page.query_selector('django-formset form:invalid') is not None
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == "Enter a valid email address."



urlpatterns.append(
    path('integer_form', FormsetView.as_view(
        template_name='form.html',
        form_class=type('IntegerForm', (Form,), {
            'name': 'integer_form',
            'integer': fields.IntegerField(
                initial=3,
                min_value=2,
                max_value=4,
                error_messages={'min_value': "Value too low."},
            )}),
        success_url='/success',
    ), name='integer_form')
)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['integer_form'])
def test_integer_field(page):
    name = 'integer'
    assert page.query_selector('django-formset form:valid') is not None
    assert page.query_selector('django-formset form:invalid') is None
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is not None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is None
    input_elem.click()
    input_elem.type("1")
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is not None
    assert page.query_selector('django-formset form:valid') is None
    assert page.query_selector('django-formset form:invalid') is not None
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == "Ensure this value is less than or equal to 4."
    input_elem.click()
    page.keyboard.press('Home')
    page.keyboard.press('Delete')
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is not None
    assert page.query_selector('django-formset form:valid') is None
    assert page.query_selector('django-formset form:invalid') is not None
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == "Value too low."


urlpatterns.append(
    path('float_form', FormsetView.as_view(
        template_name='form.html',
        form_class=type('FloatForm', (Form,), {
            'name': 'float_form',
            'float': fields.FloatField(initial=2, widget=widgets.NumberInput(attrs={'step': 0.5}))
        }),
        success_url='/success',
    ), name='float_form')
)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['float_form'])
def test_integer_field(page):
    name = 'float'
    assert page.query_selector('django-formset form:valid') is not None
    assert page.query_selector('django-formset form:invalid') is None
    input_elem = page.query_selector(f'django-formset form input[name="{name}"]')
    input_elem.click()
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is not None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is None
    input_elem.click()
    input_elem.type(".1")
    input_elem.evaluate('elem => elem.blur()')
    assert page.query_selector(f'django-formset form input[name="{name}"]:valid') is None
    assert page.query_selector(f'django-formset form input[name="{name}"]:invalid') is not None
    assert page.query_selector('django-formset form:valid') is None
    assert page.query_selector('django-formset form:invalid') is not None
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == "Input value must be a multiple of 0.5."
