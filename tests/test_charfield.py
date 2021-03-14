import pytest
import json

from django.forms import CharField, Form
from django.urls import path

from formset.views import FormsetView


class EmptyValidForm(Form):
    name = 'empty_valid'

    something = CharField(
        label="Something",
        required=False,
    )


class EmptyInvalidForm(Form):
    name = 'empty_invalid'

    something = CharField(
        label="Something",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
    )


class PrefilledValidForm(Form):
    name = 'prefilled_valid'

    something = CharField(
        label="Something",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
        initial='ABC',
    )


class PrefilledInvalidForm(Form):
    name = 'prefilled_invalid'

    something = CharField(
        label="Something",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
        initial='A',
    )


views = {
    f'form{counter}': FormsetView.as_view(
        template_name='form.html',
        form_class=form_tuple[0],
        success_url='/success',
        extra_context={'force_submission': form_tuple[1], 'withhold_messages': form_tuple[2]},
    )
    for counter, form_tuple in enumerate((form_class, force_submission, withhold_messages)
        for form_class in [EmptyValidForm, EmptyInvalidForm, PrefilledValidForm, PrefilledInvalidForm]
        for force_submission in [False, True]
        for withhold_messages in [False, True]
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
    if isinstance(form, (EmptyValidForm, PrefilledValidForm)):
        assert placeholder_text == ''
        assert input_elem_valid is not None
        assert input_elem_invalid is None
    elif isinstance(form, EmptyInvalidForm):
        assert placeholder_text == "" if withhold_messages else "This field is required."
        assert input_elem_valid is None
        assert input_elem_invalid is not None
    elif isinstance(form, PrefilledInvalidForm):
        assert placeholder_text == "" if withhold_messages else "Ensure this value has at least 2 characters."
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
    page.query_selector(f'django-formset form input[name="{name}"]:valid') is not None
    page.query_selector(f'django-formset form input[name="{name}"]:invalid') is None


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
