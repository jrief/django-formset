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
    starting_view_mode = ViewMode.weeks
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

    def get_context_hours(self, hour12, interval):
        assert interval in self.valid_intervals, f"{interval} is not a valid interval for {self.__class__}"
        start_datetime = self.start_datetime
        context = {
            'shifts': [],
        }
        interval = int(interval.total_seconds() / 60) if interval and interval < timedelta(hours=1) else None
        for shift in range(0, 24, 6):
            hours = []
            for hour in range(shift, shift + 6):
                hour_date = start_datetime.replace(hour=hour)
                if hour12:
                    hour_localized = f'{hour % 12 or 12}{hour // 12 and "pm" or "am"}'
                else:
                    hour_localized = f'{hour}h'
                if interval is None:
                    hours.append((f'{hour_date.isoformat()[:13]}:00', hour_localized, None))
                else:
                    minutes = [
                        (hour_date.replace(minute=minute).isoformat()[:16],
                        f'{hour % 12 or 12 if hour12 else hour}:{minute:02d}')
                        for minute in range(0, 60, interval)
                    ]
                    hours.append((hour_date.isoformat()[:16], hour_localized, minutes))
            context['shifts'].append(hours)
        next_day = start_datetime + timedelta(days=1)
        hour_localized = '12am' if hour12 else '24h'
        context['shifts'].append([(next_day.replace(hour=0, minute=0).isoformat()[:16], hour_localized, None)])
        context.update(
            prev_day=(start_datetime - timedelta(days=1)).isoformat()[:16],
            next_day=(start_datetime + timedelta(days=1)).isoformat()[:16],
        )
        return context

    def get_context_weeks(self):
        cal = calendar.Calendar(self.firstweekday)
        start_datetime = self.start_datetime
        context = {
            'weekdays': [],
            'monthdays': [],
        }
        safe_day = min(start_datetime.day, 28)  # prevent date arithmetic errors on adjacent months
        if start_datetime.month == 1:
            context.update(
                prev_month=start_datetime.replace(day=safe_day, month=12, year=start_datetime.year - 1).isoformat()[:16],
                next_month=start_datetime.replace(day=safe_day, month=start_datetime.month + 1).isoformat()[:16],
            )
        elif start_datetime.month == 12:
            context.update(
                prev_month=start_datetime.replace(day=safe_day, month=start_datetime.month - 1).isoformat()[:16],
                next_month=start_datetime.replace(day=safe_day, month=1, year=start_datetime.year + 1).isoformat()[:16],
            )
        else:
            context.update(
                prev_month=start_datetime.replace(day=safe_day, month=start_datetime.month - 1).isoformat()[:16],
                next_month=start_datetime.replace(day=safe_day, month=start_datetime.month + 1).isoformat()[:16],
            )
        monthdays = []
        for day in cal.itermonthdays3(start_datetime.year, start_datetime.month):
            monthday = date(*day)
            monthdays.append(monthday)
            css_classes = []
            if monthday.month != start_datetime.month:
                css_classes.append('adjacent')
            timestamp = f'{monthday.isoformat()[:10]}T00:00'
            context['monthdays'].append((timestamp, monthday.day, ' '.join(css_classes)))
        context['weekdays'] = [(date_format(day, 'D'), date_format(day, 'l')) for day in monthdays[:7]]
        return context

    def get_context_months(self):
        start_datetime = self.start_datetime
        context = {
            'months': [],
        }
        context.update(
            prev_year=start_datetime.replace(year=start_datetime.year - 1, month=1).isoformat()[:16],
            next_year=start_datetime.replace(year=start_datetime.year + 1, month=1).isoformat()[:16],
        )
        for m in range(1, 13):
            month_date = date(start_datetime.year, m, 1)
            timestamp = f'{month_date.isoformat()[:10]}T00:00'
            context['months'].append((timestamp, date_format(month_date, 'F')))
        return context

    def get_context_years(self):
        start_datetime = self.start_datetime
        context = {
            'years': [],
        }
        start_epoch = int(start_datetime.year / 20) * 20
        context.update(
            prev_epoch=start_datetime.replace(year=start_epoch - 20, month=1).isoformat()[:16],
            next_epoch=start_datetime.replace(year=start_epoch + 20, month=1).isoformat()[:16],
        )
        for y in range(start_epoch, start_epoch + 20):
            year_date = date(y, 1, 1)
            timestamp = f'{year_date.isoformat()[:10]}T00:00'
            context['years'].append((timestamp, date_format(year_date, 'Y')))
        return context

    def get_context(self, hour12=False, interval=None):
        context = {
            'startdate': self.start_datetime,
            'template': self.get_template_name(self.starting_view_mode),
        }
        context.update(self.get_context_hours(hour12, interval))
        context.update(self.get_context_weeks())
        context.update(self.get_context_months())
        context.update(self.get_context_years())
        return context

    def get_template_name(self, view_mode):
        return {
            ViewMode.hours: 'calendar/hours.html',
            ViewMode.years: 'calendar/years.html',
            ViewMode.months: 'calendar/months.html',
            ViewMode.weeks: 'calendar/weeks.html',
        }[view_mode]

    def render(self, view_mode, hour12=False, pure=False, interval=None):
        context = {
            'startdate': self.start_datetime,
        }
        if view_mode == ViewMode.hours:
            context.update(self.get_context_hours(hour12, interval))
        elif view_mode == ViewMode.years:
            context.update(self.get_context_years())
        elif view_mode == ViewMode.months:
            context.update(self.get_context_months())
        else:
            context.update(self.get_context_weeks())
        template = get_template(self.get_template_name(view_mode))
        if pure:
            context.update(template=template)
            template = get_template('calendar/range.html')
        return template.render({'calendar': context})

    @classmethod
    def parse_request(cls, request):
        """
        Parse a request object to extract the parameters for the calendar.
        """
        start_datetime = datetime.fromisoformat(request.GET.get('date'))
        hour12 = 'hour12' in request.GET
        pure = 'pure' in request.GET
        view_mode = ViewMode.frommode(request.GET.get('mode'))
        if 'interval' in request.GET:
            interval = timedelta(minutes=int(request.GET.get('interval')))
        else:
            interval = None
        return start_datetime, hour12, pure, view_mode, interval


class CalendarResponseMixin:
    """
    To be added to a view class in order to build the responses when iterating over months.
    """
    calendar_renderer_class = CalendarRenderer

    def get(self, request, **kwargs):
        if request.accepts('text/html') and 'calendar' in request.GET:
            try:
                start_datetime, hour12, pure, view_mode, interval = self.calendar_renderer_class.parse_request(request)
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Invalid parameter 'calendar'")
            cal = self.calendar_renderer_class(start_datetime=start_datetime)
            return HttpResponse(cal.render(view_mode, hour12, pure, interval))
        return super().get(request, **kwargs)
