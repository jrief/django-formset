from django.forms import fields, forms
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField

from formset.collection import AddSiblingActivator, FormCollection
from formset.fieldset import Fieldset
from formset.formfields.collection import CollectionField
from formset.formfields.richtext import RichTextField
from formset.forms import ModelForm
from formset.widgets import UploadedFileInput

from formset.widgets import CountrySelectize, Selectize, SelectizeMultiple
from django_countries import countries

from testapp.models.gallery import Gallery
from testapp.models.reporter import Reporter


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
    reporter = ModelChoiceField(
        label="Reporter",
        queryset=Reporter.objects.all(),
        widget=Selectize(
            search_lookup='full_name__icontains',
            placeholder="Main reporter"
        ),
        required=True,
    )
    extra_reporters = ModelMultipleChoiceField(
        label="Reporters",
        queryset=Reporter.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='full_name__icontains',
            placeholder="Extra reporters"
        ),
        required=False,
    )


class ImageCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    image_form = ImageForm()
    legend = "Gallery Images"
    induce_add_sibling = '.add_gallery:active'
    ignore_marked_for_removal = True

    add_gallery = AddSiblingActivator("Add other Gallery")


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
    collection = CollectionField(ImageCollection)
    # extra_collection = CollectionField(ImageCollection)
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
        fields = ['name', 'extra_data', 'collection']
        fields_map = {
            'extra_data': ['main_image', 'main_caption', 'supplement.name', 'supplement.origin'],
        }
