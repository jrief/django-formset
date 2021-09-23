from django.urls import reverse_lazy

from formset.views import FormView, FormsetView

from testapp.forms import (
    SubscribeForm, PersonForm, UploadForm, SelectForm, sample_subscribe_data,
    sample_persona_data, sample_selectize_data)


class SubscribeFormView(FormView):
    form_class = SubscribeForm
    success_url = reverse_lazy('form_data_valid')
    initial = sample_subscribe_data


class CombinedFormsView(FormsetView):
    success_url = reverse_lazy('form_data_valid')

    persona = PersonForm(initial=sample_persona_data)

    upload = UploadForm()

    select = SelectForm(initial=sample_selectize_data)
