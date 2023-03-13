#!/usr/bin/env python
"""
moonphase.py - Calculate Lunar Phase
Author: Sean B. Palmer, inamidst.com
Cf. http://en.wikipedia.org/wiki/Lunar_phase#Lunar_phase_calculation
"""

from datetime import datetime
from decimal import Decimal
import math

from django.forms import fields, forms

from formset.calendar import CalendarRenderer
from formset.widgets import DatePicker


class MoonCalendarRenderer(CalendarRenderer):
    def get_context_weeks(self):
        context = super().get_context_weeks()
        return context

    def position(self, now):
       diff = now - datetime.datetime(2001, 1, 1)
       days = Decimal(diff.days) + (Decimal(diff.seconds) / Decimal(86400))
       lunations = Decimal("0.20439731") + (days * Decimal("0.03386319269"))
       return lunations % Decimal(1)

    def phase(self, pos):
       index = (pos * Decimal(8)) + Decimal("0.5")
       index = math.floor(index)
       return {
          0: "New Moon",
          1: "Waxing Crescent",
          2: "First Quarter",
          3: "Waxing Gibbous",
          4: "Full Moon",
          5: "Waning Gibbous",
          6: "Last Quarter",
          7: "Waning Crescent"
       }[int(index) & 7]

    def main(self):
       pos = self.position(datetime.now())
       phasename = self.phase(pos)

       roundedpos = round(float(pos), 3)
       print("%s (%s)" % (phasename, roundedpos))


class MoonForm(forms.Form):
    a_date = fields.DateField(
        label="A Date",
        widget=DatePicker(calendar_renderer=MoonCalendarRenderer),
    )
