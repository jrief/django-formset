from django.forms import fields, forms

from formset.collection import FormCollection
from formset.formfields.collection import CollectionField
from formset.formfields.richtext import RichTextField
from formset.forms import ModelForm
from formset.widgets import UploadedFileInput

from testapp.models.component import Component


class SlideForm(forms.Form):
    title = fields.CharField(
        label="Slide Title",
        max_length=100,
    )
    image = fields.ImageField(
        label="Image",
        widget=UploadedFileInput,
    )
    caption = RichTextField(
        label="Caption",
        required=False,
    )


class SlidesCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    slide_form = SlideForm()
    legend = "Carousel Slides"
    add_label = "Add Carousel Slide"
    ignore_marked_for_removal = True


class CarouselForm(ModelForm):
    """
    Form to show how to use ``CollectionField`` with a ``fields_map``.
    """
    auto_start = fields.BooleanField(
        label="Auto Start",
        required=False,
    )
    interval = fields.IntegerField(
        label="Interval in milliseconds",
        min_value=1,
        required=False,
        help_text="If unset, slides do not scroll automatically.",
    )
    slides = CollectionField(SlidesCollection)

    class Meta:
        model = Component
        fields = ['context']
        fields_map = {
            'context': ['auto_start', 'interval', 'slides'],
        }
