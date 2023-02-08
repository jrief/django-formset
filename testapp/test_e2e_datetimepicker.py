from datetime import timedelta
import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.utils.timezone import datetime
from django.urls import path

from formset.views import FormView
from formset.widgets import DateTimePicker


class ScheduleForm(forms.Form):
    schedule = fields.DateTimeField(
        label="Schedule",
        widget=DateTimePicker(attrs={
            'step': timedelta(minutes=15),
        }),

    )


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class=ScheduleForm
    success_url = '/success'


urlpatterns = [
    path('new_schedule', DemoFormView.as_view(), name='new_schedule'),
    path('current_schedule', DemoFormView.as_view(initial={'schedule': datetime(2023, 2, 2, 9, 10)}), name='current_schedule'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_schedule'])
def test_datetimepicker_select(page, viewname):
    schedule_field = page.locator('django-formset input[name="schedule"]')
    calendar = page.locator('django-formset input[name="schedule"] + .dj-calendar')
    expect(calendar).not_to_be_visible()
    assert schedule_field.evaluate('elem => elem.value') == ""
    schedule_field.focus()
    expect(calendar).to_be_visible()
