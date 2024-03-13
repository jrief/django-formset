import json
import pytest
from time import sleep

from playwright.sync_api import expect

from django.conf import settings
from django.core.management import call_command
from django.forms import Form, fields, models
from django.urls import path
from django.views.generic import FormView as GenericFormView

from formset.views import IncompleteSelectResponseMixin, FormViewMixin
from formset.widgets import DualSelector, Selectize, SelectizeMultiple

from testapp.models import County, CountyUnnormalized, State


class NativeFormView(IncompleteSelectResponseMixin, FormViewMixin, GenericFormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
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
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['single_form'])
def test_one_preselection(page, mocker, viewname):
    state_field = page.locator('django-formset select[name="state"]')
    county_field = page.locator('django-formset select[name="county"]')
    expect(county_field.locator('option')).to_have_count(251)
    assert county_field.evaluate('elem => elem.value') == ''
    spy = mocker.spy(NativeFormView, 'get')
    state_field.select_option(label="Georgia")
    sleep(0.25)
    expect(county_field.locator('option')).to_have_count(0)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    spy.reset_mock()
    georgia_counties = County.objects.filter(state__name="Georgia")
    assert content['count'] == georgia_counties.count()
    page.locator('django-formset .ts-control').click()
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown')
    first_option = dropdown_element.locator(f'div[data-selectable][data-value="{georgia_counties.first().id}"]')
    assert first_option.inner_text() == str(georgia_counties.first())
    last_option = dropdown_element.locator(f'div[data-selectable][data-value="{georgia_counties.last().id}"]')
    assert last_option.inner_text() == str(georgia_counties.last())


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['multi_form'])
def test_multi_preselections(page, mocker, viewname):
    states_field = page.locator('django-formset select[name="states"]')
    counties_field = page.locator('django-formset select[name="counties"]')
    expect(counties_field.locator('option')).to_have_count(251)
    assert counties_field.evaluate('elem => elem.value') == ''
    spy = mocker.spy(NativeFormView, 'get')
    states_field.select_option(label=["Texas", "New York", "Kansas"])
    sleep(0.5)
    expect(counties_field.locator('option')).to_have_count(0)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    spy.reset_mock()
    queryset = County.objects.filter(state__name__in=["Texas", "New York", "Kansas"])
    assert content['count'] == SelectizeMultiple.max_prefetch_choices
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
    page.locator('django-formset .ts-control input').type("zap")
    sleep(0.75)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    spy.reset_mock()
    assert content['count'] == 1
    expect(zapata_option).to_have_count(1)
    expect(zapata_option).to_have_text("Zapata (TX)")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['many_form'])
def test_many_preselections(page, mocker, viewname):
    states_field = page.locator('django-formset select[name="states"]')
    counties_field = page.locator('django-formset select[name="counties"]')
    expect(counties_field.locator('option')).to_have_count(SelectizeMultiple.max_prefetch_choices)
    assert counties_field.evaluate('elem => elem.value') == ''
    spy = mocker.spy(NativeFormView, 'get')
    states_field.select_option(label=["Oregon", "Minnesota", "North Carolina", "Nebraska"])
    sleep(0.25)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    spy.reset_mock()
    assert content['count'] == SelectizeMultiple.max_prefetch_choices
    page.locator('django-formset .dj-dual-selector .left-column input').type("linc", delay=100)
    page.locator('django-formset .dj-dual-selector .dj-move-all-right').click()
    right_select = page.locator('django-formset .dj-dual-selector .right-column select')
    expect(right_select.locator('option')).to_have_count(4)
