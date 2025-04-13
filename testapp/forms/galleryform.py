from django.forms import fields, forms

from formset.collection import FormCollection
from formset.formfields.collection import CollectionField
from formset.fieldset import Fieldset
from formset.forms import ModelForm
from formset.richtext.fields import RichTextField
from formset.richtext.widgets import RichTextarea
from formset.widgets import UploadedFileInput

from formset.widgets import CountrySelectize
from django_countries import countries

from testapp.models.gallery import Gallery


class SingleForm(forms.Form):
    text = fields.CharField(label="Text")
    image = fields.ImageField(
        label="Next",
        required=False,
        widget=UploadedFileInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ImageForm(forms.Form):
    image = fields.ImageField(
        label="Image",
        required=True,
        widget=UploadedFileInput,
    )
    caption = RichTextField(
        label="Caption",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SingleText(FormCollection):
    single_text = SingleForm()


class ImageCollection(CollectionField):
    min_siblings = 0
    extra_siblings = 1
    image_form = ImageForm()
    text_form = SingleText()
    legend = "Gallery Images"
    add_label = "Add other Gallery"
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
    main_image = fields.ImageField(
        label="Image",
        required=True,
        widget=UploadedFileInput,
    )
    main_caption = RichTextField(
        label="Main Caption",
        required=False,
    )
    supplement = Supplement()

    class Meta:
        model = Gallery
        fields = ['name', 'extra_data']
        fields_map = {
            'extra_data': ['main_image', 'main_caption', 'image_collection', 'supplement.name', 'supplement.origin'],
        }
