from formset.widgets import DateCalendar, DatePicker, DateTextbox, DateTimeCalendar, DateTimePicker, DateTimeTextbox


class DateRangeCalendar(DateCalendar):
    template_name = 'formset/default/widgets/calendar.html'

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateRangePicker(DatePicker):
    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateRangeTextbox(DateTextbox):
    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)


class DateTimeRangeCalendar(DateTimeCalendar):
    template_name = 'formset/default/widgets/calendar.html'

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateTimeRangePicker(DateTimePicker):
    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateTimeRangeTextbox(DateTimeTextbox):
    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)
