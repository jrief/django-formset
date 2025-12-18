from django.forms import fields, widgets
from django.forms.models import ModelForm

from formset.collection import AddSiblingActivator, FormCollection
from formset.widgets import UploadedFileInput

from testapp.models.gallery import Image, Gallery


class ImageForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    class Meta:
        model = Image
        fields = ['id', 'image', 'caption']
        widgets = {
            'image': UploadedFileInput,
        }


class ImageCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    image = ImageForm()
    legend = "Gallery Images"
    induce_add_sibling = '.add_image:active'
    related_field = 'gallery'

    add_image = AddSiblingActivator("Add Image")

    def get_or_create_instance(self, data):
        if data := data.get('image'):
            try:
                return self.instance.images.get(id=data.get('id') or 0), False
            except (AttributeError, Image.DoesNotExist, ValueError):
                form = ImageForm(data=data)
                if form.is_valid():
                    return Image(image=form.cleaned_data['image'], gallery=self.instance), False
        return None, False


class GalleryForm(ModelForm):
    class Meta:
        model = Gallery
        fields = ['name']


class GalleryCollection(FormCollection):
    """
    Shows how to use a FormCollection for models.
    """

    gallery = GalleryForm()
    images = ImageCollection()
