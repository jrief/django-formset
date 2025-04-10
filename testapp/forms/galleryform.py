from django.forms import fields, forms

from formset.fields.collection import CollectionField
from formset.fieldset import Fieldset
from formset.forms import ModelForm
from formset.richtext.fields import RichTextField
from formset.richtext.widgets import RichTextarea
from formset.widgets import UploadedFileInput

from formset.widgets import CountrySelectize
from django_countries import countries

from testapp.models.gallery import Gallery


class ImageForm(forms.Form):
    image = fields.ImageField(
        label="Image",
        required=True,
        widget=UploadedFileInput,
    )
    caption = fields.CharField(
        label="Caption",
        required=False,
        widget=RichTextarea,
    )


class ImageCollection(CollectionField):
    min_siblings = 0
    extra_siblings = 1
    image = ImageForm()
    legend = "Gallery Images"
    add_label = "Add Image"
    ignore_marked_for_removal = True


class Supplement(Fieldset):
    legend = "Other Fields"

    name = fields.CharField(
        label="Name",
        max_length=100,
        required=False,
    )
    origin = fields.ChoiceField(
        label="Country of Origin",
        widget=CountrySelectize,
        choices=countries,
    )


class GalleryImageForm(ModelForm):
    image_collection = ImageCollection()
    image = fields.ImageField(
        label="Image",
        required=True,
        widget=UploadedFileInput,
    )
    caption = RichTextField(
        label="Caption",
        required=False,
    )
    supplement = Supplement()

    class Meta:
        model = Gallery
        fields = ['name', 'extra_data']
        fields_map = {
            #'extra_data': ['image'],
            'extra_data': ['image', 'caption', 'image_collection', 'supplement.name', 'supplement.origin'],
        }
