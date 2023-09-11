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
    In this form we replace the calendar renderer against our own implementation. This allows us
    to use our own context when rendering the calendar.
    """

    some_date = fields.DateField(
        label="Some Date",
        widget=DatePicker(calendar_renderer=MoonCalendarRenderer),
    )
