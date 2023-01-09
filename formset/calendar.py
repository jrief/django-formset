import calendar
from datetime import date

from django.shortcuts import render
from django.utils.formats import date_format


def get_calendar_context(firstweekday=calendar.MONDAY, start_date=None):
    cal = calendar.Calendar(firstweekday)
    if start_date is None:
        start_date = date.today()
    context = {
        'startdate': start_date.replace(day=1),
        'months': [date_format(date(start_date.year, m, 1), 'F') for m in range(1, 13)],
        'weekdays': [],
        'monthdays': [],
    }
    for day in cal.itermonthdays3(start_date.year, start_date.month):
        monthday = date(*day)
        css_class = 'adjacent' if monthday.month != start_date.month else None
        context['monthdays'].append((monthday, css_class))
    for day, classes in context['monthdays'][:7]:
        context['weekdays'].append((date_format(day, 'D'), date_format(day, 'l')))
    return context


class CalendarResponseMixin:
    """
    To be added to a view class in order to build the responses when iterating over months.
    """
    def get(self, request, **kwargs):
        if request.accepts('text/html') and 'calendar' in request.GET:
            start_date = date.fromisoformat(request.GET.get('calendar'))
            context = {'calendar': get_calendar_context(start_date=start_date)}
            return render(request, 'formset/components/calendar.html', context)
        return super().get(request, **kwargs)
