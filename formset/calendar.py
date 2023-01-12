import calendar
from datetime import date, timedelta
from enum import Enum

from django.shortcuts import render
from django.http.response import HttpResponseBadRequest
from django.utils.formats import date_format


class ViewMode(Enum):
    weeks = 'w'
    months = 'm'
    years = 'y'

    @classmethod
    def frommode(cls, value):
        for val in cls.__members__.values():
            if val.value.lower() == value:
                return val
        raise KeyError(value)


def get_calendar_context(firstweekday=calendar.MONDAY, start_date=None):
    cal = calendar.Calendar(firstweekday)
    if start_date is None:
        start_date = date.today()
    start_date = start_date.replace(day=1)
    context = {
        'startdate': start_date,
        'weekdays': [],
        'monthdays': [],
        'months': [],
        'years': [],
        'today': date.today().replace(day=1).isoformat()[:10],
    }
    if start_date.month == 1:
        context.update(
            prev_month=start_date.replace(month=12, year=start_date.year - 1),
            next_month=start_date.replace(month=start_date.month + 1),
        )
    elif start_date.month == 12:
        context.update(
            prev_month=start_date.replace(month=start_date.month - 1),
            next_month=start_date.replace(month=1, year=start_date.year + 1),
        )
    else:
        context.update(
            prev_month=start_date.replace(month=start_date.month - 1).isoformat()[:10],
            next_month=start_date.replace(month=start_date.month + 1).isoformat()[:10],
        )
    start_epoch = int(start_date.year / 20) * 20
    context.update(
        prev_year=start_date.replace(year=start_date.year - 1, month=1).isoformat()[:10],
        next_year=start_date.replace(year=start_date.year + 1, month=1).isoformat()[:10],
        prev_epoch=start_date.replace(year=start_epoch - 20, month=1).isoformat()[:10],
        next_epoch=start_date.replace(year=start_epoch + 20, month=1).isoformat()[:10],
    )
    for y in range(start_epoch, start_epoch + 20):
        year_date = date(y, 1, 1)
        context['years'].append((year_date.isoformat()[:10], date_format(year_date, 'Y')))
    for m in range(1, 13):
        month_date = date(start_date.year, m, 1)
        context['months'].append((month_date.isoformat()[:10], date_format(month_date, 'F')))
    monthdays = []
    for day in cal.itermonthdays3(start_date.year, start_date.month):
        monthday = date(*day)
        monthdays.append(monthday)
        css_class = 'adjacent' if monthday.month != start_date.month else None
        context['monthdays'].append((monthday.isoformat()[:10], monthday.day, css_class))
    context['weekdays'] = [(date_format(day, 'D'), date_format(day, 'l')) for day in monthdays[:7]]
    return context


class CalendarResponseMixin:
    """
    To be added to a view class in order to build the responses when iterating over months.
    """
    def get(self, request, **kwargs):
        if request.accepts('text/html') and 'calendar' in request.GET:
            try:
                start_date = date.fromisoformat(request.GET.get('date'))
                view_mode = ViewMode.frommode(request.GET.get('mode'))
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid parameter 'calendar'")
            if view_mode == ViewMode.weeks:
                template_name = 'calendar/weeks.html'
            elif view_mode == ViewMode.months:
                template_name = 'calendar/months.html'
            else:
                template_name = 'calendar/years.html'
            context = {'calendar': get_calendar_context(start_date=start_date)}
            return render(request, template_name, context)
        return super().get(request, **kwargs)
