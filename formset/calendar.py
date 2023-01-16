import calendar
from datetime import date
from enum import Enum

from django.http.response import HttpResponse, HttpResponseBadRequest
from django.template.loader import get_template
from django.utils.formats import date_format
from django.utils.timezone import datetime


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


class CalendarRenderer:
    def __init__(self, firstweekday=calendar.MONDAY, start_datetime=None):
        self.firstweekday = firstweekday
        if isinstance(start_datetime, datetime):
            self.start_datetime = start_datetime
        else:
            self.start_datetime = datetime.now()

    def get_context(self):
        cal = calendar.Calendar(self.firstweekday)
        start_datetime = self.start_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context = {
            'startdate': start_datetime,
            'weekdays': [],
            'monthdays': [],
            'months': [],
            'years': [],
            'today': date.today().isoformat()[:10],
        }
        if start_datetime.month == 1:
            context.update(
                prev_month=start_datetime.replace(month=12, year=start_datetime.year - 1).isoformat()[:10],
                next_month=start_datetime.replace(month=start_datetime.month + 1).isoformat()[:10],
            )
        elif start_datetime.month == 12:
            context.update(
                prev_month=start_datetime.replace(month=start_datetime.month - 1).isoformat()[:10],
                next_month=start_datetime.replace(month=1, year=start_datetime.year + 1).isoformat()[:10],
            )
        else:
            context.update(
                prev_month=start_datetime.replace(month=start_datetime.month - 1).isoformat()[:10],
                next_month=start_datetime.replace(month=start_datetime.month + 1).isoformat()[:10],
            )
        start_epoch = int(start_datetime.year / 20) * 20
        context.update(
            prev_year=start_datetime.replace(year=start_datetime.year - 1, month=1).isoformat()[:10],
            next_year=start_datetime.replace(year=start_datetime.year + 1, month=1).isoformat()[:10],
            prev_epoch=start_datetime.replace(year=start_epoch - 20, month=1).isoformat()[:10],
            next_epoch=start_datetime.replace(year=start_epoch + 20, month=1).isoformat()[:10],
        )
        for y in range(start_epoch, start_epoch + 20):
            year_date = date(y, 1, 1)
            context['years'].append((year_date.isoformat()[:10], date_format(year_date, 'Y')))
        for m in range(1, 13):
            month_date = date(start_datetime.year, m, 1)
            context['months'].append((month_date.isoformat()[:10], date_format(month_date, 'F')))
        monthdays = []
        for day in cal.itermonthdays3(start_datetime.year, start_datetime.month):
            monthday = date(*day)
            monthdays.append(monthday)
            css_class = 'adjacent' if monthday.month != start_datetime.month else None
            context['monthdays'].append((monthday.isoformat()[:10], monthday.day, css_class))
        context['weekdays'] = [(date_format(day, 'D'), date_format(day, 'l')) for day in monthdays[:7]]
        return context

    def render(self, view_mode):
        if view_mode == ViewMode.weeks:
            template_name = 'calendar/weeks.html'
        elif view_mode == ViewMode.months:
            template_name = 'calendar/months.html'
        else:
            template_name = 'calendar/years.html'
        template = get_template(template_name)
        context = {'calendar': self.get_context()}
        return HttpResponse(template.render(context))


class CalendarResponseMixin:
    """
    To be added to a view class in order to build the responses when iterating over months.
    """
    calendar_renderer_class = CalendarRenderer

    def get(self, request, **kwargs):
        if request.accepts('text/html') and 'calendar' in request.GET:
            try:
                start_datetime = datetime.fromisoformat(request.GET.get('date'))
                view_mode = ViewMode.frommode(request.GET.get('mode'))
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid parameter 'calendar'")
            cal = self.calendar_renderer_class(start_datetime=start_datetime)
            return cal.render(view_mode)
        return super().get(request, **kwargs)
