from django.contrib.gis.forms import PointField
from django import forms

from formset.formfields.geomap import GeoMapField


class FountainForm(forms.Form):
    map = GeoMapField()

