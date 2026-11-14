from django.forms import fields, forms

from formset.collection import AddSiblingActivator, FormCollection
from formset.formfields.collection import CollectionField
from formset.formfields.richtext import RichTextField
from formset.forms import ModelForm
from formset.widgets import UploadedFileInput

from formset.fieldset import Fieldset

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
    induce_add_sibling = '.add_slide:active'
    ignore_marked_for_removal = True

    add_slide = AddSiblingActivator("Add Carousel Slide")


from django.contrib.auth import get_user_model
from django.forms.models import ModelChoiceField


class AuthorFieldset(Fieldset):
    user = ModelChoiceField(
        label="User",
        queryset=get_user_model().objects.all(),
        required=False,
    )
    display_name = fields.CharField(
        label="Display Name",
        required=False,
    )


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
    author = AuthorFieldset(legend="Author")
    slides = CollectionField(SlidesCollection)

    class Meta:
        model = Component
        fields = ['context']
        fields_map = {
            'context': ['auto_start', 'interval', 'author.user', 'author.display_name', 'slides'],
        }
