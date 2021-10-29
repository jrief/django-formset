from django.forms import forms, fields
from formset.collection import FormCollection

from .person import PersonForm, sample_person_data
from .opinion import OpinionForm, sample_opinion_data


class DoubleFormCollection(FormCollection):
    extra_siblings = 1
    max_siblings = 8

    persona = PersonForm()

    # upload = UploadForm()


class TripleFormCollection(FormCollection):
    min_siblings = 0

    double = DoubleFormCollection()# initial=[{'persona': sample_personb_data}])

    opinion = OpinionForm(initial=sample_opinion_data)


class ConfirmForm(forms.Form):
    accept = fields.BooleanField(
        label="Accept terms and conditions",
        initial=False,
    )


class NestedCollection(FormCollection):
    triple = TripleFormCollection()

    confirm = ConfirmForm()


class MultipleCollection(FormCollection):
    double = DoubleFormCollection(initial=[{'persona': sample_person_data}])
