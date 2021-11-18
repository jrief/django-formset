from django.forms import forms, fields
from formset.collection import FormCollection

from .contact import PersonForm
from .opinion import OpinionForm, sample_opinion_data
from .person import sample_person_data


class DoubleFormCollection(FormCollection):
    min_siblings = 2
    max_siblings = 8

    persona = PersonForm(initial=sample_person_data)

    # upload = UploadForm()


class TripleFormCollection(FormCollection):
    min_siblings = 2

    double = DoubleFormCollection(initial=[{'persona': sample_person_data}, {'persona': sample_person_data}])

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
    double = DoubleFormCollection()
