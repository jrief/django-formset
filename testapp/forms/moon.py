from datetime import datetime
from decimal import Decimal
import math

from django.forms import fields, forms

from formset.calendar import CalendarRenderer, ViewMode
from formset.widgets import DatePicker


class MoonCalendarRenderer(CalendarRenderer):
    """
    Calculate lunar phase and use it as context for the calendar
    Author: Sean B. Palmer, inamidst.com
    Cf. http://en.wikipedia.org/wiki/Lunar_phase#Lunar_phase_calculation
    """
    phases = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

    def position(self, then):
        diff = then - datetime(2001, 1, 1)
        days = Decimal(diff.days) + Decimal(diff.seconds) / Decimal(86400)
        lunations = Decimal('0.20439731') + days * Decimal('0.03386319269')
        return lunations % Decimal(1)

    def phase(self, pos):
        index = pos * Decimal(8) + Decimal('0.5')
        index = int(math.floor(index)) & 7
        return self.phases[index]

    def get_template_name(self, view_mode):
        if view_mode == ViewMode.weeks:
            return 'calendar/weeks-moon.html'
        return super().get_template_name(view_mode)

    def get_context_weeks(self):
        context = super().get_context_weeks()
        monthdays = []
        for monthday in context['monthdays']:
            phase = self.phase(self.position(datetime.fromisoformat(monthday[0])))
            monthdays.append((*monthday, phase))
        context['monthdays'] = monthdays
        return context


class MoonForm(forms.Form):
    """
    In this form we replace the calendar renderer against our own implementation. This can be
    useful whenever we need to modify the context, depending on events occuring at various dates.
    This for instance can be useful to display vacant or occupied rooms in a booking application.
    Or it can be useful to display extra information such as holidays.

    In this example we modify the context to show the phases of the moon, by adopting the calendar
    renderer:

        .. code-block:: python

            from django.forms import fields, forms
            from formset.widgets import DatePicker
            from formset.calendar import CalendarRenderer

            class MoonCalendarRenderer(CalendarRenderer):
                def get_context_weeks(self):
                    # custom implementation
                    # ...

            class MoonForm(...):
                some_date = fields.DateField(
                    widget=DatePicker(
                        calendar_renderer=MoonCalendarRenderer
                    ),
                )

    Since the calendar is
    """

    some_date = fields.DateField(
        label="Some Date",
        widget=DatePicker(calendar_renderer=MoonCalendarRenderer),
    )
