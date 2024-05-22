from datetime import timedelta
from time import sleep
import json
import pytest
from playwright.sync_api import expect

from django.forms import forms
from django.utils.timezone import datetime
from django.urls import path

from formset.calendar import CalendarResponseMixin
from formset.views import FormView
from formset.ranges import DateRangeField, DateRangeCalendar, DateTimeRangeField, DateTimeRangePicker

from .utils import get_javascript_catalog


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

    )


class DemoFormView(CalendarResponseMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('booking', DemoFormView.as_view(form_class=BookingForm), name='booking'),
    path('reservation', DemoFormView.as_view(form_class=ReservationForm), name='reservation'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['booking'])
def test_daterange_initial(page, mocker, viewname):
    calendar = page.locator('django-formset input[name="range"] + .dj-calendar')
    expect(calendar).to_be_visible()
    expect(calendar.locator('li[data-date="2023-08-08"]')).to_have_class('selected')
    background_color = calendar.locator('li[data-date="2023-08-07"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'rgba(0, 0, 0, 0)'
    background_color = calendar.locator('li[data-date="2023-08-09"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'rgb(185, 246, 255)'
    expect(calendar.locator('.aside-left > time')).to_be_empty()
    expect(calendar.locator('.aside-right > time')).to_have_text('Tue Oct 10 2023')
    calendar.locator('button.prev').click()
    sleep(0.2)
    expect(calendar.locator('.aside-right > time')).to_have_text('Tue Aug 08 2023')
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.extend > time')).to_have_text('July 2023')
    calendar.locator('button.extend').click()
    sleep(0.2)
    expect(calendar.locator('ul.months li.selected')).to_have_count(2)
    background_color = calendar.locator('li[data-date="2023-09-01"]').evaluate('elem => window.getComputedStyle(elem).getPropertyValue("background-color")')
    assert background_color == 'rgb(185, 246, 255)'
    calendar.locator('li[data-date="2023-09-01"]').click()
    sleep(0.2)
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.extend > time')).to_have_text('September 2023')
    calendar.locator('button.next').click()
    sleep(0.2)
    expect(calendar.locator('li[data-date="2023-10-10"]')).to_have_class('selected')
    expect(calendar.locator('.aside-left > time')).to_have_text('Tue Aug 08 2023')
    calendar.locator('button.next').click()
    sleep(0.2)
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(0)
    expect(calendar.locator('.aside-left > time')).to_have_text('Tue Oct 10 2023')
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['range'] == ['2023-08-08', '2023-10-10']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['booking'])
def test_daterange_set(page, mocker, viewname):
    calendar = page.locator('django-formset input[name="range"] + .dj-calendar')
    expect(calendar).to_be_visible()
    calendar.locator('button.today').click()
    sleep(0.3)
    expect(calendar.locator('ul.monthdays li.today')).to_be_visible()
    today = datetime.today()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(1)
    if today.day < 15:
        other = (today + timedelta(days=9)).strftime('%Y-%m-%d')
    else:
        other = (today - timedelta(days=9)).strftime('%Y-%m-%d')
    calendar.locator(f'ul.monthdays li[data-date="{other}"]').hover()
    calendar.locator(f'ul.monthdays li[data-date="{other}"]').click()
    expect(calendar.locator('ul.monthdays li.selected')).to_have_count(2)
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    request = json.loads(spy.call_args.args[1].body)
    if today.day < 15:
        assert request['formset_data']['range'] == [today.strftime('%Y-%m-%d'), other]
    else:
        assert request['formset_data']['range'] == [other, today.strftime('%Y-%m-%d')]
