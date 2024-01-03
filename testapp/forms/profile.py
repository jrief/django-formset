from django.forms import fields, forms

from formset.collection import FormCollection
from formset.dialog import DialogForm
from formset.fields import Button
from formset.widgets import UploadedFileInput


class CustomerForm(forms.Form):
    username = fields.CharField()
    edit_profile = Button(
        label="Edit my Profile",
        help_text = "Open the dialog to edit the profile",
    )


class ProfileForm(DialogForm):
    title = "Edit Profile"
    open_condition = 'customer.username == "admin" || customer.edit_profile:active'

    full_name = fields.CharField(
        label="First Name",
        max_length=100,
    )
    email = fields.EmailField(
        label="Email",
    )
    picture = fields.ImageField(
        label="Picture",
        required=False,
        widget=UploadedFileInput,
    )


class ProfileCollection(FormCollection):
    legend = "Collection with Dialog Form"
    customer = CustomerForm()

    extra_profile = Button()

    profile = ProfileForm()
