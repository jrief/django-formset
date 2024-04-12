from datetime import timedelta
from time import sleep
import pytest
from playwright.sync_api import expect

from django import VERSION as DJANGO_VERSION
from django.forms import fields, forms
from django.utils.timezone import datetime
from django.urls import path

from formset.calendar import CalendarResponseMixin
from formset.views import FormView
from formset.widgets import DateTimePicker


class ScheduleForm(forms.Form):
    schedule = fields.DateTimeField(
        label="Schedule",
        widget=DateTimePicker(attrs={
            'step': timedelta(minutes=15),
        }),

    )


class DemoFormView(CalendarResponseMixin, FormView):
    template_name = 'testapp/native-form.html'
    form_class=ScheduleForm
    success_url = '/success'


schedule_datetime = datetime(2023, 2, 13, 9, 10)

urlpatterns = [
    path('new_schedule', DemoFormView.as_view(), name='new_schedule'),
    path('current_schedule', DemoFormView.as_view(initial={'schedule': schedule_datetime}), name='current_schedule'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('locale', ['en-US', 'de-DE', 'ja-JP'])
@pytest.mark.parametrize('viewname', ['new_schedule'])
def test_datetimepicker_set(page, mocker, viewname, locale):
    now = datetime.now()
    schedule_field = page.locator('django-formset input[name="schedule"]')
    textbox = page.locator('django-formset input[name="schedule"] + [role="textbox"]')
    opener = page.locator('django-formset input[name="schedule"] + [role="textbox"] > .calendar-picker-indicator')
    calendar = page.locator('django-formset input[name="schedule"] + [role="textbox"] + .dj-calendar')
    expect(schedule_field).to_have_value('')
    expect(calendar).not_to_be_visible()
    opener.click()
    expect(calendar).to_be_visible()
    today_li = calendar.locator('ul.monthdays > li.today')
    expect(today_li).to_be_visible()
    today_string = now.date().isoformat()
    assert today_li.get_attribute('data-date') == today_string
    spy = mocker.spy(DemoFormView, 'get')
    today_li.click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert querydict.get('date') == today_string
    assert querydict.get('mode') == 'h'
    assert querydict.get('interval') == '15'
    spy.reset_mock()
    hour_li = calendar.locator('ul.hours > li.today')
    aria_label = hour_li.get_attribute('aria-label')
    minutes_ul = calendar.locator(f'ul.minutes[aria-labelledby="{aria_label}"]')
    expect(minutes_ul).not_to_be_visible()
    hour_li.click()
    sleep(0.2)
    assert spy.called is False
    expect(minutes_ul).to_be_visible()
    minute_li = minutes_ul.locator('li:nth-of-type(4)')
    minute_string = f'{now.isoformat()[:13]}:45'
    assert minute_li.get_attribute('data-date') == minute_string
    minute_li.click()
    new_date = schedule_field.evaluate('elem => elem.valueAsDate').replace(tzinfo=None)
    assert new_date == now.replace(minute=45, second=0, microsecond=0)
    if locale == 'en-US':
        expect(textbox).to_have_text(datetime.strftime(now, '%m/%d/%Y %H:45').replace(' 00:45', ' 24:45'))
    elif locale == 'de-DE':
        expect(textbox).to_have_text(datetime.strftime(now, '%d.%m.%Y %H:45'))
    elif locale == 'ja-JP':
        expect(textbox).to_have_text(datetime.strftime(now, '%Y/%m/%d %H:45'))
    else:
        expect(textbox).to_have_text(datetime.strftime(now, '%Y-%m-%d %H:45'))


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('locale', ['en-US', 'de-DE', 'ja-JP'])
@pytest.mark.parametrize('viewname', ['current_schedule'])
def test_datetimepicker_change(page, mocker, viewname, locale):
    schedule_field = page.locator('django-formset input[name="schedule"]')
    textbox = page.locator('django-formset input[name="schedule"] + [role="textbox"]')
    opener = page.locator('django-formset input[name="schedule"] + [role="textbox"] > .calendar-picker-indicator')
    calendar = page.locator('django-formset input[name="schedule"] + [role="textbox"] + .dj-calendar')
    expect(calendar).not_to_be_visible()
    if locale == 'en-US':
        expect(textbox).to_have_text(datetime.strftime(schedule_datetime, '%m/%d/%Y %H:%M'))
    elif locale == 'de-DE':
        expect(textbox).to_have_text(datetime.strftime(schedule_datetime, '%d.%m.%Y %H:%M'))
    elif locale == 'ja-JP':
        expect(textbox).to_have_text(datetime.strftime(schedule_datetime, '%Y/%m/%d %H:%M'))
    else:
        expect(textbox).to_have_text(datetime.strftime(schedule_datetime, '%Y-%m-%d %H:%M'))
    opener.click()
    expect(calendar).to_be_visible()
    spy = mocker.spy(DemoFormView, 'get')
    calendar.locator('button.next').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-13'
    assert querydict.get('mode') == 'w'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    extend_button = calendar.locator('button.extend')
    expect(extend_button).to_have_text("March 2023")
    extend_button.click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-13'
    assert querydict.get('mode') == 'm'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    extend_button = calendar.locator('button.extend')
    expect(extend_button).to_have_text("2023")
    extend_button.click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-13'
    assert querydict.get('mode') == 'y'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    expect(calendar.locator('.controls time[datetime]')).to_have_text("2020 – 2039")
    calendar.locator('.controls button.narrow').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-13'
    assert querydict.get('mode') == 'm'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    calendar.locator('ul.months li[data-date="2023-07-01"]').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-07-01'
    assert querydict.get('mode') == 'w'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    calendar.locator('ul.monthdays li[data-date="2023-07-09"]').click()
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-07-09'
    assert querydict.get('mode') == 'h'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    calendar.locator('ul.hours li[aria-label="2023-07-09T13:00"]').click()
    calendar.locator('ul.minutes li[data-date="2023-07-09T13:15"]').click()
    expect(calendar).not_to_be_visible()
    changed_datetime = datetime(2023, 7, 9, 13, 15)
    if locale == 'en-US':
        expect(textbox).to_have_text(datetime.strftime(changed_datetime, '%m/%d/%Y %H:%M'))
    elif locale == 'de-DE':
        expect(textbox).to_have_text(datetime.strftime(changed_datetime, '%d.%m.%Y %H:%M'))
    elif locale == 'ja-JP':
        expect(textbox).to_have_text(datetime.strftime(changed_datetime, '%Y/%m/%d %H:%M'))
    else:
        expect(textbox).to_have_text(datetime.strftime(changed_datetime, '%Y-%m-%d %H:%M'))


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['current_schedule'])
def test_datetimepicker_navigate(page, mocker, viewname):
    opener = page.locator('django-formset input[name="schedule"] + [role="textbox"] > .calendar-picker-indicator')
    calendar = page.locator('django-formset input[name="schedule"] + [role="textbox"] + .dj-calendar')
    expect(calendar).not_to_be_visible()
    opener.click()
    expect(calendar).to_be_visible()
    expect(calendar.locator('ul.monthdays li.selected')).to_be_visible()
    page.keyboard.press('ArrowRight')
    selected_date = datetime.fromisoformat(calendar.locator('ul.monthdays li.selected').get_attribute('data-date'))
    assert selected_date.date() == datetime(2023, 2, 14).date()
    page.keyboard.press('ArrowDown')
    selected_date = datetime.fromisoformat(calendar.locator('ul.monthdays li.selected').get_attribute('data-date'))
    assert selected_date.date() == datetime(2023, 2, 21).date()
    page.keyboard.press('ArrowDown')
    spy = mocker.spy(DemoFormView, 'get')
    page.keyboard.press('ArrowRight')
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-01'
    assert querydict.get('mode') == 'w'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    expect(calendar.locator('ul.monthdays li.selected')).to_have_attribute('data-date', '2023-03-01')
    page.keyboard.press('ArrowDown')
    page.keyboard.press('ArrowLeft')
    page.keyboard.press('Enter')
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    querydict = spy.call_args.args[1].GET
    assert 'calendar' in querydict
    assert querydict.get('date') == '2023-03-07'
    assert querydict.get('mode') == 'h'
    assert querydict.get('interval') == '15'
    spy.reset_mock()

    page.keyboard.press('ArrowDown')
    expect(calendar.locator('ul.hours > li.constricted')).to_have_attribute('aria-label', '2023-03-07T01:00')
    page.keyboard.press('ArrowLeft')
    expect(calendar.locator('ul.minutes > li.selected')).to_have_attribute('data-date', '2023-03-07T00:45')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('language', ['en', 'de', 'fr', 'es', 'pt'])
@pytest.mark.parametrize('viewname', ['current_schedule'])
def test_datetimepicker_i18n(page, settings, viewname, language):
    calendar = page.locator('django-formset input[name="schedule"] + [role="textbox"] + .dj-calendar')
    opener = page.locator('django-formset input[name="schedule"] + [role="textbox"] > .calendar-picker-indicator')
    expect(calendar).not_to_be_visible()
    opener.click()
    sleep(0.2)
    expect(calendar).to_be_visible()
    title = calendar.locator('.controls time[datetime]')
    wednesday = calendar.locator('.weekdays li:nth-of-type(3)')
    if language == 'de':
        expect(title).to_have_text("Februar 2023")
        expect(wednesday).to_have_text("Mi")
    elif language == 'en':
        expect(title).to_have_text("February 2023")
        expect(wednesday).to_have_text("Wed")
    elif language == 'fr':
        expect(title).to_have_text("février 2023")
        expect(wednesday).to_have_text("mer")
    elif language == 'es':
        if DJANGO_VERSION < (4, 1):
            expect(title).to_have_text("Febrero 2023")
            expect(wednesday).to_have_text("Mié")
        else:
            expect(title).to_have_text("febrero 2023")
            expect(wednesday).to_have_text("mié")
    elif language == 'pt':
        expect(title).to_have_text("Fevereiro 2023")
        expect(wednesday).to_have_text("Qua")
