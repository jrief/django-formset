from django.forms import fields, widgets
from django.forms.models import ModelForm

from formset.collection import FormCollection
from formset.widgets import UploadedFileInput
from testapp.models.gallery import Image, Gallery


class ImageForm(ModelForm):
    id = fields.IntegerField(
        required=False,
        widget=widgets.HiddenInput,
    )

    image = fields.FileField(
        label="Image",
        widget=UploadedFileInput,
        required=False,
    )

    class Meta:
        model = Image
        fields = ['id', 'image']


class ImageCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    image = ImageForm()
    legend = "Gallery Images"
    add_label = "Add Image"
    related_field = 'gallery'

    def retrieve_instance(self, data):
        if data := data.get('image'):
            try:
                return self.instance.images.get(id=data.get('id') or 0)
            except (AttributeError, Image.DoesNotExist, ValueError):
                return Image(image=data.get('image'), gallery=self.instance)


class GalleryForm(ModelForm):
    class Meta:
        model = Gallery
        fields = '__all__'


class GalleryCollection(FormCollection):
    gallery = GalleryForm()
    images = ImageCollection()
