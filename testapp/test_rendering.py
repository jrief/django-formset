import pytest

from bs4 import BeautifulSoup

from django.forms import fields, forms, widgets
from django.test import RequestFactory

from formset.renderers.default import FormRenderer as DefaultFormRenderer
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.renderers.bulma import FormRenderer as BulmaFormRenderer
from formset.renderers.foundation import FormRenderer as FoundationFormRenderer
from formset.renderers.tailwind import FormRenderer as TailwindFormRenderer
from formset.renderers.uikit import FormRenderer as UIKitFormRenderer
from formset.utils import FormMixin
from formset.views import FormView

from .sampledata import sample_subscribe_data
from .validators import validate_password


http_request = RequestFactory().get('/')


class SubscribeForm(forms.Form):
    name = 'subscribe'

    CONTINENT_CHOICES = [
        ('', "––– please select –––"), ('am', "America"), ('eu', "Europe"), ('as', "Asia"),
        ('af', "Africa"), ('au', "Australia"), ('oc', "Oceania"), ('an', 'Antartica'),
    ]

    TRANSPORTATION_CHOICES = [
        ("Private Transport", [('foot', "Foot"), ('bike', "Bike"), ('mc', "Motorcycle"), ('car', "Car")]),
        ("Public Transport", [('taxi', "Taxi"), ('bus', "Bus"), ('train', "Train"), ('ship', "Ship"), ('air', "Airplane")]),
    ]

    NOTIFY_BY = [
        ('postal', "Letter"), ('email', "EMail"), ('phone', "Phone"), ('sms', "SMS"),
    ]

    last_name = fields.CharField(
        label="Last name",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
    )

    first_name = fields.RegexField(
        r'^[A-Z][a-z -]*$',
        label="First name",
        error_messages={'invalid': "A first name must start in upper case."},
        help_text="Must start in upper case followed by one or more lowercase characters.",
    )

    gender = fields.ChoiceField(
        label="Gender",
        choices=[('m', "Male"), ('f', "Female")],
        widget=widgets.RadioSelect,
        error_messages={'invalid_choice': "Please select your gender."},
    )

    email = fields.EmailField(
        label="E-Mail",
        help_text="Please enter a valid email address",
    )

    subscribe = fields.BooleanField(
        label="Subscribe Newsletter",
        initial=False,
        required=False,
    )

    phone = fields.RegexField(
        r'^\+?[0-9 .-]{4,25}$',
        label="Phone number",
        error_messages={'invalid': "Phone number have 4-25 digits and may start with '+'."},
        widget=fields.TextInput(attrs={'hide-if': 'subscribe'})
    )

    birth_date = fields.DateField(
        label="Date of birth",
        widget=widgets.DateInput(attrs={'type': 'date', 'pattern': r'\d{4}-\d{2}-\d{2}'}),
        help_text="Allowed date format: yyyy-mm-dd",
    )

    continent = fields.ChoiceField(
        label="Living on continent",
        choices=CONTINENT_CHOICES,
        required=True,
        initial='',
        error_messages={'invalid_choice': "Please select your continent."},
    )

    weight = fields.IntegerField(
        label="Weight in kg",
        min_value=42,
        max_value=95,
        error_messages={'min_value': "You are too lightweight.", 'max_value': "You are too obese."},
    )

    height = fields.FloatField(
        label="Height in meters",
        min_value=1.45,
        max_value=1.95,
        widget=widgets.NumberInput(attrs={'step': 0.01}),
        error_messages={'max_value': "You are too tall."},
    )

    used_transportation = fields.MultipleChoiceField(
        label="Used Tranportation",
        choices=TRANSPORTATION_CHOICES,
        widget=widgets.CheckboxSelectMultiple,
        required=True,
        help_text="Used means of tranportation.",
    )

    preferred_transportation = fields.ChoiceField(
        label="Preferred Transportation",
        choices=TRANSPORTATION_CHOICES,
        widget=widgets.RadioSelect,
        help_text="Preferred mean of tranportation.",
    )

    available_transportation = fields.MultipleChoiceField(
        label="Available Tranportation",
        choices=TRANSPORTATION_CHOICES,
        help_text="Available means of tranportation.",
    )

    notifyme = fields.MultipleChoiceField(
        label="Notification",
        choices=NOTIFY_BY,
        widget=widgets.CheckboxSelectMultiple,
        required=True,
        help_text="Must choose at least one type of notification",
    )

    annotation = fields.CharField(
        label="Annotation",
        required=True,
        widget=widgets.Textarea(attrs={'cols': '80', 'rows': '3'}),
    )

    agree = fields.BooleanField(
        label="Agree with our terms and conditions",
        initial=False,
    )

    password = fields.CharField(
        label="Password",
        widget=widgets.PasswordInput,
        validators=[validate_password],
        help_text="The password is 'secret'",
    )

    confirmation_key = fields.CharField(
        max_length=40,
        required=True,
        widget=widgets.HiddenInput(),
        initial='hidden value',
    )


class SubscribeFormView(FormView):
    success_url = '/success'


@pytest.fixture(scope='session', params=['default', 'bootstrap', 'bulma', 'foundation', 'tailwind', 'uikit'])
def framework(request):
    return request.param


@pytest.fixture(scope='session', params=[{}, sample_subscribe_data])
def initial(request):
    return request.param


@pytest.fixture(scope='session')
def native_view(framework, initial):
    return SubscribeFormView.as_view(
        template_name='testapp/native-form.html',
        form_class=SubscribeForm,
        initial=initial,
        extra_context={'framework': framework}
    )


@pytest.fixture(scope='session', params=[
    DefaultFormRenderer, BootstrapFormRenderer, BulmaFormRenderer, FoundationFormRenderer, TailwindFormRenderer, UIKitFormRenderer])
def extended_view(request, initial):
    form_class = type(SubscribeForm.__name__, (FormMixin, SubscribeForm), {'default_renderer': request.param})
    return SubscribeFormView.as_view(
        template_name='testapp/extended-form.html',
        form_class=form_class,
        initial=initial,
    )


def check_field(framework, form, field_name, soup, initial):
    form_name = form.name
    bf = form[field_name]
    initial_value = initial.get(field_name) if initial else None
    field_elem = soup.find(id=f'{form_name}_id_{field_name}')
    assert field_elem is not None
    widget_type = 'textarea' if isinstance(bf.field.widget, widgets.Textarea) else bf.field.widget.input_type
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
        assert bf.label == label.text.strip().rstrip(':')
        if allow_multiple_selected and widget_type == 'checkbox' or widget_type == 'radio':
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
        if widget_type in ['text', 'email', 'number', 'date', 'textarea', 'password']:
            assert 'form-control' in field_elem.attrs['class']
        elif widget_type in ['select']:
            assert 'form-select' in field_elem.attrs['class']
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


@pytest.fixture(scope='session')
def native_soup(native_view):
    response = native_view(http_request)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    view_initkwargs = native_view.view_initkwargs
    framework = view_initkwargs['extra_context']['framework']
    form_class = view_initkwargs['form_class']
    initial = view_initkwargs['initial'] if 'initial' in view_initkwargs else None
    return framework, form_class, soup, initial


@pytest.fixture(scope='session')
def extended_soup(extended_view):
    response = extended_view(http_request)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    view_initkwargs = extended_view.view_initkwargs
    form_class = view_initkwargs['form_class']
    initial = view_initkwargs['initial'] if 'initial' in view_initkwargs else None
    return form_class, soup, initial


@pytest.mark.parametrize('field_name', SubscribeForm.base_fields.keys())
def test_field_from_native_form(native_soup, field_name):
    framework, form_class, soup, initial = native_soup
    assert not issubclass(form_class, FormMixin)
    form = type(form_class.__name__, (FormMixin, form_class), {})()
    check_field(framework, form, field_name, soup, initial)


@pytest.mark.parametrize('field_name', SubscribeForm.base_fields.keys())
def test_field_from_extended_form(extended_soup, field_name):
    form_class, soup, initial = extended_soup
    assert issubclass(form_class, FormMixin)
    framework = form_class.default_renderer.__module__.split('.')[-1]
    check_field(framework, form_class(), field_name, soup, initial)
