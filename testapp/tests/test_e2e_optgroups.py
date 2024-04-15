import pytest
from time import sleep
from playwright.sync_api import expect

from django.conf import settings
from django.core.management import call_command
from django.forms import Form, fields, models
from django.urls import path
from django.views.generic import UpdateView, FormView as GenericFormView

from formset.views import IncompleteSelectResponseMixin, FormViewMixin
from formset.widgets import DualSelector, Selectize, SelectizeMultiple, DualSortableSelector

from testapp.forms.county import CountyForm
from testapp.models import County, CountyUnnormalized, State


class NativeFormView(IncompleteSelectResponseMixin, FormViewMixin, GenericFormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


class ModelFormView(IncompleteSelectResponseMixin, FormViewMixin, UpdateView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'
    form_class = CountyForm
    model = County

    def get_object(self, queryset=None):
        obj, _ = self.model.objects.get_or_create(created_by='testapp')
        return obj


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', settings.BASE_DIR / 'testapp/fixtures/counties.json', verbosity=0)
        for county in CountyUnnormalized.objects.all():
            state, _ = State.objects.get_or_create(code=county.state_code, name=county.state_name)
            County.objects.create(state=state, name=county.county_name)


def initial_static_choices():
    choices, num_choices = [], 0
    for state in State.objects.all():
        choices.append((state.name, [(c.id, str(c)) for c in County.objects.filter(state=state)[:21:7]]))
        num_choices += len(choices[-1][1])
        if num_choices > 225:
            break
    return choices


test_fields = dict(
    static_county=fields.ChoiceField(
        choices=initial_static_choices,
        widget=Selectize(),
    ),
    one_county=models.ModelChoiceField(
        label="One County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
            group_field_name='state',
        ),
        required=True,
    ),
    few_counties = models.ModelMultipleChoiceField(
        label="A few counties",
        queryset=County.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='name__icontains',
            group_field_name='state',
            max_items=20,
        ),
        required=True,
    ),
    many_counties=models.ModelMultipleChoiceField(
        label="Many counties",
        queryset=County.objects.all(),
        widget=DualSelector(
            search_lookup='name__icontains',
            group_field_name='state',
        ),
        required=True,
    ),
    sortable_counties=models.ModelMultipleChoiceField(
        label="Sortable counties",
        queryset=County.objects.all(),
        widget=DualSortableSelector(
            search_lookup='name__icontains',
            group_field_name='state',
        ),
        required=True,
    ),
)

views = {
    name: NativeFormView.as_view(
        form_class=type(f'{name}_form', (Form,), {'name': name, 'county': field}),
    )
    for (name, field) in test_fields.items()
}

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.fixture
def view(viewname):
    return views[viewname]


@pytest.fixture
def form(view):
    return view.view_initkwargs['form_class']()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['static_county', 'one_county'])
def test_single_county(page, form, viewname):
    selectize = page.locator('django-formset select[is="django-selectize"]')
    optgroups = selectize.locator('optgroup')
    states = [optgroups.nth(i).get_attribute('label') for i in range(optgroups.count())]
    if viewname == 'static_county':
        assert len(states) == 51
        states[50] == "Wyoming"
    else:
        assert len(states) == 6
        states[4] == "California"
    input_field = page.locator('django-formset input[type="text"]')
    input_field.type("gosh")
    sleep(0.3)  # tom-select's loadThrottle is set to 300ms
    div_optgroup = page.locator('django-formset .ts-dropdown .optgroup')
    expect(div_optgroup.locator('.optgroup-header')).to_have_text("Wyoming")
    div_option = div_optgroup.locator('[role="option"]')
    expect(div_option).to_have_text("Goshen (WY)")
    div_option.click()
    value = selectize.evaluate('elem => elem.value')
    assert County.objects.get(id=value).name == "Goshen"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['few_counties'])
def test_few_counties(page, form, viewname):
    selectize = page.locator('django-formset select[is="django-selectize"]')
    optgroups = selectize.locator('optgroup')
    states = [optgroups.nth(i).get_attribute('label') for i in range(optgroups.count())]
    assert len(states) == 6
    states[4] == "California"
    input_field = page.locator('django-formset input[type="text"]')
    input_field.type("clall")
    sleep(0.3)  # tom-select's loadThrottle is set to 300ms
    div_optgroup = page.locator('django-formset .ts-dropdown .optgroup .optgroup-header')
    expect(div_optgroup).to_have_text("Washington")
    div_option = page.locator('django-formset .ts-dropdown .optgroup [role="option"]')
    expect(div_option).to_have_text("Clallam (WA)")
    div_option.click()
    for _ in range(5):
        page.keyboard.press("Backspace")
    input_field.type("tillam")
    sleep(0.3)  # tom-select's loadThrottle is set to 300ms
    expect(div_optgroup).to_have_text("Oregon")
    expect(div_option).to_have_text("Tillamook (OR)")
    div_option.click()
    for _ in range(6):
        page.keyboard.press("Backspace")
    input_field.type("stani")
    sleep(0.3)  # tom-select's loadThrottle is set to 300ms
    expect(div_optgroup).to_have_text("California")
    expect(div_option).to_have_text("Stanislaus (CA)")
    div_option.click()
    for _ in range(5):
        page.keyboard.press("Backspace")
    input_field.type("lync")
    sleep(0.3)  # tom-select's loadThrottle is set to 300ms
    expect(div_optgroup).to_have_text("Virginia")
    expect(div_option).to_have_text("Lynchburg (VA)")
    div_option.click()
    values = selectize.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    expected = County.objects.filter(id__in=values).order_by('name').values_list('name', flat=True)
    assert list(expected) == ["Clallam", "Lynchburg", "Stanislaus", "Tillamook"]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['many_counties'])
def test_many_counties(page, form, viewname):
    selector = page.locator('django-formset select[is="django-dual-selector"]')
    select_left = page.locator('django-formset .left-column select[multiple]')
    select_right = page.locator('django-formset .right-column select[multiple]')
    expect(select_left.locator('optgroup')).to_have_count(6)
    expect(select_left.locator('option')).to_have_count(250)
    expect(select_right.locator('optgroup')).to_have_count(0)
    expect(select_right.locator('option')).to_have_count(0)
    select_left.locator('optgroup:nth-child(3) option:nth-child(10)').dblclick()
    expect(select_left.locator('optgroup')).to_have_count(6)
    expect(select_left.locator('option')).to_have_count(249)
    expect(select_right.locator('optgroup')).to_have_count(1)
    expect(select_right.locator('option')).to_have_count(1)
    assert select_right.locator('optgroup').get_attribute('label') == "Arizona"
    expect(select_right.locator('optgroup:nth-child(1) option')).to_have_text("Navajo (AZ)")
    expected = select_right.locator('optgroup:nth-child(1) option').get_attribute('value')
    assert selector.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)') == [expected]
    select_left.locator('optgroup:nth-child(6) option:first-child').click()
    select_left.locator('optgroup:nth-child(6) option:last-child').click(modifiers=['Shift'])
    page.locator('django-formset button.dj-move-selected-right ').click()
    expect(select_right.locator('optgroup')).to_have_count(2)
    expect(select_right.locator('option')).to_have_count(6)
    assert select_right.locator('optgroup:last-child').get_attribute('label') == "Colorado"
    expect(select_right.locator('optgroup:last-child option:first-child')).to_have_text("Adams (CO)")
    select_right.locator('optgroup:first-child option').dblclick()
    expect(select_right.locator('optgroup')).to_have_count(1)
    expect(select_right.locator('option')).to_have_count(5)
    expected = [select_right.locator(f'optgroup option:nth-child({i})').get_attribute('value') for i in range(1, 6)]
    assert selector.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)') == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sortable_counties'])
def test_sortable_counties(page, form, viewname):
    selector = page.locator('django-formset select[is="django-dual-selector"]')
    select_left = page.locator('django-formset .left-column select[multiple]')
    select_right = page.locator('django-formset .right-column django-sortable-select')
    expect(select_left.locator('optgroup')).to_have_count(6)
    expect(select_left.locator('option')).to_have_count(250)
    expect(select_right.locator('optgroup')).to_have_count(0)
    expect(select_right.locator('option')).to_have_count(0)
    select_left.locator('optgroup').nth(5).locator('option').first.click()
    select_left.locator('optgroup').nth(5).locator('option').last.click(modifiers=['Shift'])
    page.locator('django-formset button.dj-move-selected-right ').click()
    expect(select_right.locator('optgroup')).to_have_count(1)
    expect(select_right.locator('option')).to_have_count(5)
    assert select_right.locator('optgroup').get_attribute('label') == "Colorado"
    expect(select_right.locator('optgroup option').first).to_have_text("Adams (CO)")
    expect(select_right.locator('optgroup option').last).to_have_text("Baca (CO)")
    before = [select_right.locator('optgroup option').nth(i).get_attribute('value') for i in range(5)]
    select_right.locator('optgroup').first.locator('option').last.drag_to(select_right.locator('optgroup').first.locator('option').first)
    sleep(0.4)  # Sortable.js has a delay of 300ms
    select_right.locator('optgroup').first.locator('option').nth(1).drag_to(select_right.locator('optgroup').locator('option').last)
    sleep(0.4)  # Sortable.js has a delay of 300ms
    after = [select_right.locator('optgroup option').nth(i).get_attribute('value') for i in range(5)]
    before.insert(0, before.pop(4))  # emulate dragging
    before.append(before.pop(1))
    assert after == before
    assert selector.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)') == after
