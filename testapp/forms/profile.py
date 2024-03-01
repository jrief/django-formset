from django.forms import fields, forms

from formset.collection import FormCollection
from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button, UploadedFileInput


class UserNameForm(forms.Form):
    username = fields.CharField()
    edit_profile = Activator(
        label="Edit my Profile",
        help_text="Open the dialog to edit the profile",
    )


class ProfileForm(DialogForm):
    title = "Edit Profile"
    induce_open = 'customer.username == "admin" || extra_profile:active || customer.edit_profile:active'
    induce_close = '.dismiss:active || .submit:active'

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
    dismiss = Activator(
        label="Close",
        widget=Button(
            action='close',
        ),
    )
    submit = Activator(
        label="Save",
        widget=Button(
            action='apply',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )


class ProfileCollection(FormCollection):
    legend = "Collection with Dialog Form"
    customer = UserNameForm()

    extra_profile = Activator(
        label="Extra Profile Button",
        help_text="Open the dialog to edit the profile",
    )

    profile = ProfileForm()
