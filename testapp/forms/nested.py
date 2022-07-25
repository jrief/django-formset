from django.forms.fields import CharField
from django.forms.forms import Form
from formset.collection import FormCollection


class CampumForm(Form):
    agro = CharField(
        label="Agro",
        min_length=2,
        max_length=12,
    )


class NestedCollection3(FormCollection):
    min_siblings = 1
    max_siblings = 4
    extra_siblings = 2

    campum = CampumForm()


class NestedCollection2(FormCollection):
    campum = CampumForm()

    level3 = NestedCollection3()


class NestedCollection1(FormCollection):
    campum = CampumForm()

    level2 = NestedCollection2()


class NestedCollection(FormCollection):
    min_siblings = 1
    max_siblings = 5
    extra_siblings = 1

    campum = CampumForm()

    level1 = NestedCollection1()
