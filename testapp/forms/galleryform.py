from django.forms import fields, forms

from formset.collection import FormCollection
from formset.forms import ModelForm
from formset.richtext.fields import RichTextField
from formset.richtext.widgets import RichTextarea
from formset.widgets import UploadedFileInput

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


class ImageCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    image = ImageForm()
    legend = "Gallery Images"
    add_label = "Add Image"
    ignore_marked_for_removal = True


class GalleryForm(ModelForm):
    # images = ImageCollection()
    image = fields.ImageField(
        label="Image",
        required=True,
        widget=UploadedFileInput,
    )
    # caption = RichTextField(
    #     label="Caption",
    #     required=False,
    # )

    class Meta:
        model = Gallery
        fields = ['name', 'extra_data']
        fields_map = {
            'extra_data': ['image'],
        }
