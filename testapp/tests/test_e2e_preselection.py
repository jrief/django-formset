import pytest
from re import compile as regex

from playwright.sync_api import expect

from django.core.management import call_command
from django.forms import Form, fields, models
from django.urls import path
from django.views.generic import FormView as GenericFormView

from formset.views import IncompleteSelectResponseMixin, FormViewMixin
from formset.widgets import DualSelector, Selectize, SelectizeMultiple

from testapp.models import County, CountyUnnormalized, State

from .utils import ContextMixin, get_javascript_catalog


class NativeFormView(ContextMixin, IncompleteSelectResponseMixin, FormViewMixin, GenericFormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker, settings):
    with django_db_blocker.unblock():
        call_command('loaddata', settings.BASE_DIR / 'testapp/fixtures/counties.json', verbosity=0)
        for county in CountyUnnormalized.objects.all():
            state, _ = State.objects.get_or_create(code=county.state_code, name=county.state_name)
            County.objects.create(state=state, name=county.county_name)


def initial_state_choices():
    choices = [('', "–––––")]
    choices.extend((state.id, state.name) for state in State.objects.all())
    return choices


class SingleForm(Form):
    state = fields.ChoiceField(
        choices=initial_state_choices,
        required=False,
    )

    county=models.ModelChoiceField(
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
            filter_by={'state': 'state__id'},
        ),
    )


class MultiForm(Form):
    states = fields.MultipleChoiceField(
        choices=lambda: [(state.id, state.name) for state in State.objects.all()],
        required=False,
    )

    counties=models.ModelMultipleChoiceField(
        queryset=County.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='name__icontains',
            filter_by={'states': 'state__id'},
        ),
    )


class ManyForm(Form):
    states = fields.MultipleChoiceField(
        choices=lambda: [(state.id, state.name) for state in State.objects.all()],
        required=False,
    )

    counties=models.ModelMultipleChoiceField(
        queryset=County.objects.all(),
        widget=DualSelector(
            search_lookup='name__icontains',
            filter_by={'states': 'state__id'},
        ),
    )


views = {
    'single_form': NativeFormView.as_view(
        form_class=SingleForm,
    ),
    'multi_form': NativeFormView.as_view(
        form_class=MultiForm,
    ),
    'many_form': NativeFormView.as_view(
        form_class=ManyForm,
    ),
}

# urlpatterns = [path(name, view, name=name) for name, view in views.items()]

urlpatterns = [
    path('single_form', NativeFormView.as_view(form_class=SingleForm), name='single_form'),
    path('multi_form', NativeFormView.as_view(form_class=MultiForm), name='multi_form'),
    path('many_form', NativeFormView.as_view(form_class=ManyForm), name='many_form'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['single_form'])
def test_one_preselection(page, viewname):
    state_field = page.locator('django-formset select[name="state"]')
    county_field = page.locator('django-formset select[name="county"]')
    expect(county_field.locator('option')).to_have_count(251)
    assert county_field.evaluate('elem => elem.value') == ''
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        state_field.select_option(label="Georgia")
    assert response_info.value.ok is True
    expect(county_field.locator('option')).to_have_count(0)
    georgia_counties = County.objects.filter(state__name="Georgia")
    assert response_info.value.json()['count'] == georgia_counties.count()
    page.locator('django-formset .ts-control').click()
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown')
    first_option = dropdown_element.locator(f'div[data-selectable][data-value="{georgia_counties.first().id}"]')
    assert first_option.inner_text() == str(georgia_counties.first())
    last_option = dropdown_element.locator(f'div[data-selectable][data-value="{georgia_counties.last().id}"]')
    assert last_option.inner_text() == str(georgia_counties.last())


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['multi_form'])
def test_multi_preselections(page, viewname):
    states_field = page.locator('django-formset select[name="states"]')
    counties_field = page.locator('django-formset select[name="counties"]')
    expect(counties_field.locator('option')).to_have_count(251)
    assert counties_field.evaluate('elem => elem.value') == ''
    selected_states = ["Texas", "New York", "Kansas"]
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        states_field.select_option(label=selected_states)
    assert response_info.value.ok is True
    assert response_info.value.json()['count'] == SelectizeMultiple.max_prefetch_choices
    expect(counties_field.locator('option')).to_have_count(0)
    queryset = County.objects.filter(state__name__in=selected_states)
    assert response_info.value.json()['count'] == SelectizeMultiple.max_prefetch_choices
    page.locator('django-formset .ts-control').click()
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown')
    first_option = dropdown_element.locator(f'div[data-selectable][data-value="{queryset.first().id}"]')
    assert first_option.inner_text() == str(queryset.first())
    last_county = queryset[SelectizeMultiple.max_prefetch_choices - 1]
    last_option = dropdown_element.locator(f'div[data-selectable][data-value="{last_county.id}"]')
    expect(last_option).to_have_text(str(last_county))
    zapata_county = County.objects.get(name="Zapata")
    zapata_option = dropdown_element.locator(f'div[data-selectable][data-value="{zapata_county.id}"]')
    expect(zapata_option).to_have_count(0)
    input_field = page.locator('django-formset .ts-dropdown .dropdown-input-wrap input[type="text"]')
    expect(input_field).not_to_be_visible()
    page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control').click()
    expect(input_field).to_be_visible()
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        input_field.type("zap")
    assert response_info.value.ok is True
    assert response_info.value.json()['count'] == 1
    expect(zapata_option).to_have_count(1)
    expect(zapata_option).to_have_text("Zapata (TX)")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['many_form'])
def test_many_preselections(page, viewname):
    states_field = page.locator('django-formset select[name="states"]')
    counties_field = page.locator('django-formset select[name="counties"]')
    expect(counties_field.locator('option')).to_have_count(SelectizeMultiple.max_prefetch_choices)
    assert counties_field.evaluate('elem => elem.value') == ''
    selected_states = ["Oregon", "Minnesota", "North Carolina", "Nebraska"]
    look_for = "linc"
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        states_field.select_option(label=selected_states)
    assert response_info.value.ok is True
    assert response_info.value.json()['count'] == SelectizeMultiple.max_prefetch_choices
    page.locator('django-formset .df-dual-selector .left-column input').type(look_for, delay=100)
    page.locator('django-formset .df-dual-selector button[aria-label="move all right"]').click()
    right_select = page.locator('django-formset .df-dual-selector .right-column select')
    state_ids = State.objects.filter(name__in=selected_states).values_list('id', flat=True)
    county_ids = County.objects.filter(state__id__in=state_ids, name__icontains=look_for).values_list('id', flat=True)
    expect(right_select.locator('option')).to_have_count(county_ids.count())
    assert set(counties_field.evaluate('elem => elem.value').split(',')) == set(map(str, county_ids))
