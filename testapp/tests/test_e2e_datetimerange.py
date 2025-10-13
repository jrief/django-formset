from datetime import timedelta
import pytest
from playwright.sync_api import expect
from re import compile as regex

from django.forms import forms
from django.utils.timezone import datetime
from django.urls import path

from formset.calendar import CalendarResponseMixin
from formset.views import FormView
from formset.formfields import DateRangeField, DateTimeRangeField
from formset.widgets import DateRangeCalendar, DateTimeRangePicker

from .utils import ContextMixin, get_javascript_catalog


class BookingForm(forms.Form):
    range = DateRangeField(
        initial=(
            datetime(2023, 8, 8).date(),
            datetime(2023, 10, 10).date(),
        ),
        widget=DateRangeCalendar(),
    )


class ReservationForm(forms.Form):
    schedule = DateTimeRangeField(
        widget=DateTimeRangePicker(attrs={
            'step': timedelta(minutes=15),
        }),
        initial=(
            datetime(2025, 7, 9, 9, 15),
            datetime(2025, 9, 7, 16, 45),
        ),
    )


class DemoFormView(ContextMixin, CalendarResponseMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('booking', DemoFormView.as_view(form_class=BookingForm), name='booking'),
    path('reservation', DemoFormView.as_view(form_class=ReservationForm), name='reservation'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['booking'])
def test_daterange_initial(page, viewname):
    calendar = page.locator('django-formset input[name="range"] + .dj-calendar')
    expect(calendar).to_be_visible()
    expect(calendar.locator('li[data-date="2023-08-08T00:00"]')).to_have_class('selected')
    background_color = calendar.locator('li[data-date="2023-08-07T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'rgba(0, 0, 0, 0)'
    background_color = calendar.locator('li[data-date="2023-08-09T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'color(srgb 0.6472 0.80272 0.9928)'
    expect(calendar.locator('.aside-left > time')).to_be_empty()
    expect(calendar.locator('.aside-right > time')).to_have_text('Tue Oct 10 2023')
    calendar.locator('button.prev').click()
    expect(calendar.locator('.aside-right > time')).to_have_text('Tue Aug 08 2023')
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.extend > time')).to_have_text('July 2023')
    calendar.locator('button.extend').click()
    expect(calendar.locator('ul.months li.selected')).to_have_count(2)
    background_color = calendar.locator('li[data-date="2023-09-01T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'color(srgb 0.6472 0.80272 0.9928)'
    calendar.locator('li[data-date="2023-09-01T00:00"]').click()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.extend > time')).to_have_text('September 2023')
    calendar.locator('button.next').click()
    expect(calendar.locator('li[data-date="2023-10-10T00:00"]')).to_have_class('selected')
    expect(calendar.locator('.aside-left > time')).to_have_text('Tue Aug 08 2023')
    calendar.locator('button.next').click()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.aside-left > time')).to_have_text('Tue Oct 10 2023')
    with page.expect_response(page.url) as response_info:
        page.locator('django-formset').evaluate('elem => elem.submit()')
    assert response_info.value.ok is True
    post_data = response_info.value.request.post_data_json
    assert post_data['formset_data']['range'] == ['2023-08-08', '2023-10-10']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['booking'])
def test_daterange_set(page, viewname):
    calendar = page.locator('django-formset input[name="range"] + .dj-calendar')
    expect(calendar).to_be_visible()
    calendar.locator('button.today').click()
    expect(calendar.locator('ul.monthdays li.today')).to_be_visible()
    today = datetime.today()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(1)
    if today.day < 15:
        other = (today + timedelta(days=9)).strftime('%Y-%m-%d')
    else:
        other = (today - timedelta(days=9)).strftime('%Y-%m-%d')
    calendar.locator(f'ul.monthdays li[data-date="{other}T00:00"]').hover()
    calendar.locator(f'ul.monthdays li[data-date="{other}T00:00"]').click()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(2)
    with page.expect_response(page.url) as response_info:
        page.locator('django-formset').evaluate('elem => elem.submit()')
    assert response_info.value.ok is True
    post_data = response_info.value.request.post_data_json
    if today.day < 15:
        assert post_data['formset_data']['range'] == [today.strftime('%Y-%m-%d'), other]
    else:
        assert post_data['formset_data']['range'] == [other, today.strftime('%Y-%m-%d')]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['reservation'])
def test_datetimerange_initial(page, viewname):
    calendar = page.locator('django-formset input[name="schedule"] ~ .dj-calendar')
    expect(calendar).not_to_be_visible()
    calendar_picker = page.locator('django-formset input[name="schedule"] ~ [role="textbox"] > .calendar-picker-indicator')
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        calendar_picker.click()
    assert response_info.value.ok is True
    expect(calendar).to_be_visible()
    expect(calendar.locator('li[data-date="2025-07-09T00:00"]')).to_have_class('selected')
    background_color = calendar.locator('li[data-date="2025-07-08T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'rgba(0, 0, 0, 0)'
    background_color = calendar.locator('li[data-date="2025-07-10T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'color(srgb 0.6472 0.80272 0.9928)'
    with page.expect_response(regex(rf'^{page.url}\?.+$')) as response_info:
        calendar.locator('button.prev').click()
    assert response_info.value.ok is True
    expect(calendar.locator('.extend > time')).to_have_text('June 2025')
    calendar.locator('button.extend').click()
    expect(calendar.locator('ul.months li[data-date="2025-07-01T00:00"]')).to_have_class('selected')
    background_color = calendar.locator('li[data-date="2025-08-01T00:00"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'color(srgb 0.6472 0.80272 0.9928)'
    expect(calendar.locator('ul.months li[data-date="2025-09-01T00:00"]')).to_have_class('selected')
