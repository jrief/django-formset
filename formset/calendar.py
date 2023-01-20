import calendar
from datetime import date, timedelta
from enum import Enum

from django.conf import settings
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.template.loader import get_template
from django.utils.formats import date_format
from django.utils.timezone import datetime


class ViewMode(Enum):
    hours = 'h'
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
    valid_intervals = [
        None,
        timedelta(minutes=5),
        timedelta(minutes=10),
        timedelta(minutes=15),
        timedelta(minutes=20),
        timedelta(minutes=30),
        timedelta(hours=1),
        timedelta(days=1),
    ]

    def __init__(self, firstweekday=None, start_datetime=None):
        self.firstweekday = settings.FIRST_DAY_OF_WEEK if firstweekday is None else firstweekday
        if isinstance(start_datetime, datetime):
            self.start_datetime = start_datetime
        else:
            self.start_datetime = datetime.now()

    def get_context(self, interval):
        assert interval in self.valid_intervals, f"{interval} is not a valid interval for the calendar"
        cal = calendar.Calendar(self.firstweekday)
        start_datetime = self.start_datetime
        context = {
            'startdate': start_datetime,
            'shifts': [],
            'weekdays': [],
            'monthdays': [],
            'months': [],
            'years': [],
            'today': date.today().isoformat()[:10],
        }
        for shift in range(0, 24, 6):
            hours = []
            for hour in range(shift, shift + 6):
                hour_date = start_datetime.replace(hour=hour)
                if interval and interval < timedelta(hours=1):
                    minutes = [(hour_date.replace(minute=minute).isoformat()[:16], f'{minute:02d}')
                               for minute in range(0, 60, int(interval.total_seconds() / 60))]
                else:
                    minutes = None
                hours.append((hour_date.isoformat()[:16], hour, minutes))
            context['shifts'].append(hours)
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
            safe_day = min(start_datetime.day, 28)  # prevent date arithmetic errors on adjacent months
            context.update(
                prev_month=start_datetime.replace(day=safe_day, month=start_datetime.month - 1).isoformat()[:10],
                next_month=start_datetime.replace(day=safe_day, month=start_datetime.month + 1).isoformat()[:10],
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

    def render(self, view_mode, interval):
        if view_mode == ViewMode.hours:
            template_name = 'calendar/hours.html'
        elif view_mode == ViewMode.years:
            template_name = 'calendar/years.html'
        elif view_mode == ViewMode.months:
            template_name = 'calendar/months.html'
        else:
            template_name = 'calendar/weeks.html'
        template = get_template(template_name)
        context = {'calendar': self.get_context(interval)}
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
                if 'interval' in request.GET:
                    interval = timedelta(minutes=int(request.GET.get('interval')))
                else:
                    interval = None
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid parameter 'calendar'")
            cal = self.calendar_renderer_class(start_datetime=start_datetime)
            return cal.render(view_mode, interval)
        return super().get(request, **kwargs)
