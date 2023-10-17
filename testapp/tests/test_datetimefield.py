from bs4 import BeautifulSoup
from datetime import timedelta

import pytest

from django.utils.timezone import datetime

from formset.calendar import CalendarRenderer, ViewMode


@pytest.mark.parametrize('hour12', [False, True])
def test_render_hours(hour12):
    start_datetime = datetime(2023, 1, 18)
    interval = timedelta(minutes=15)
    cal = CalendarRenderer(start_datetime=start_datetime)
    html = cal.render(ViewMode.hours, hour12=hour12, interval=interval)
    soup = BeautifulSoup(html, features='html.parser')

    controls = soup.find(class_='controls')
    prev_button = next(controls.children)
    assert prev_button.attrs['data-date'] == '2023-01-17'
    assert 'prev' in prev_button.attrs['class']
    extend_button = prev_button.next_sibling
    assert extend_button.attrs['data-date'] == start_datetime.isoformat()
    today_button = extend_button.next_sibling
    assert today_button
    next_button = today_button.next_sibling
    assert next_button.attrs['data-date'] == '2023-01-19'
    assert 'next' in next_button.attrs['class']

    sheet_body = soup.find(class_='sheet-body')
    hours = sheet_body.find(class_='hours')
    if hour12:
        assert str(hours.contents[0]) == '<li aria-label="2023-01-18T00:00">12am</li>'
        assert str(hours.contents[5]) == '<li aria-label="2023-01-18T05:00">5am</li>'
    else:
        assert str(hours.contents[0]) == '<li aria-label="2023-01-18T00:00">0h</li>'
        assert str(hours.contents[5]) == '<li aria-label="2023-01-18T05:00">5h</li>'
    assert len(hours.contents) == 6
    minutes = hours.find_next_sibling(class_='minutes').find_all('li')
    if hour12:
        assert str(minutes[0]) == '<li data-date="2023-01-18T00:00">12:00</li>'
        assert str(minutes[3]) == '<li data-date="2023-01-18T00:45">12:45</li>'
    else:
        assert str(minutes[0]) == '<li data-date="2023-01-18T00:00">0:00</li>'
        assert str(minutes[3]) == '<li data-date="2023-01-18T00:45">0:45</li>'
    assert len(minutes) == 4


def test_render_weeks():
    start_datetime = datetime(2023, 1, 18)
    cal = CalendarRenderer(start_datetime=start_datetime)
    soup = BeautifulSoup(cal.render(ViewMode.weeks), features='html.parser')

    controls = soup.find(class_='controls')
    prev_button = next(controls.children)
    assert prev_button.attrs['data-date'] == '2022-12-18'
    extend_button = prev_button.next_sibling
    assert extend_button.attrs['data-date'] == start_datetime.isoformat()
    today_button = extend_button.next_sibling
    assert today_button
    next_button = today_button.next_sibling
    assert next_button.attrs['data-date'] == '2023-02-18'

    sheet_body = soup.find(class_='sheet-body')
    weekdays = sheet_body.find('ul', class_='weekdays')
    assert str(weekdays.contents[0]) == '<li><abbr title="Monday">Mon</abbr></li>'
    assert str(weekdays.contents[6]) == '<li><abbr title="Sunday">Sun</abbr></li>'
    monthdays = sheet_body.find(class_='monthdays')
    assert str(monthdays.contents[0]) == '<li class="adjacent" data-date="2022-12-26">26</li>'
    assert str(monthdays.contents[24]) == '<li data-date="2023-01-19">19</li>'
    assert str(monthdays.contents[41]) == '<li class="adjacent" data-date="2023-02-05">5</li>'
    assert len(monthdays.contents) == 42


def test_render_months():
    start_datetime = datetime(2023, 1, 18)
    cal = CalendarRenderer(start_datetime=start_datetime)
    soup = BeautifulSoup(cal.render(ViewMode.months), features='html.parser')

    controls = soup.find(class_='controls')
    prev_button = next(controls.children)
    assert prev_button.attrs['data-date'] == '2022-01-18'
    back_button = prev_button.next_sibling
    assert back_button.attrs['data-date'] == '2023-01-18T00:00:00'
    extend_button = back_button.next_sibling
    assert extend_button.attrs['data-date'] == start_datetime.isoformat()
    today_button = extend_button.next_sibling
    assert today_button
    next_button = today_button.next_sibling
    assert next_button.attrs['data-date'] == '2024-01-18'

    sheet_body = soup.find(class_='sheet-body')
    months = sheet_body.find('ul', class_='months')
    assert str(months.contents[0]) == '<li data-date="2023-01-01">January</li>'
    assert str(months.contents[11]) == '<li data-date="2023-12-01">December</li>'
    assert len(months.contents) == 12


def test_render_years():
    start_datetime = datetime(2023, 1, 18)
    cal = CalendarRenderer(start_datetime=start_datetime)
    soup = BeautifulSoup(cal.render(ViewMode.years), features='html.parser')

    controls = soup.find(class_='controls')
    prev_button = next(controls.children)
    assert prev_button.attrs['data-date'] == '2000-01-18'
    back_button = prev_button.next_sibling
    assert back_button.attrs['data-date'] == '2023-01-18T00:00:00'
    current = back_button.next_sibling
    assert current.attrs['datetime'] == start_datetime.isoformat()
    today_button = current.next_sibling
    assert today_button
    next_button = today_button.next_sibling
    assert next_button.attrs['data-date'] == '2040-01-18'

    sheet_body = soup.find(class_='sheet-body')
    years = sheet_body.find('ul', class_='years')
    assert str(years.contents[0]) == '<li data-date="2020-01-01">2020</li>'
    assert str(years.contents[3]) == '<li data-date="2023-01-01">2023</li>'
    assert str(years.contents[19]) == '<li data-date="2039-01-01">2039</li>'
    assert len(years.contents) == 20
