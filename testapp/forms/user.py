from django.forms.fields import IntegerField
from django.forms.models import ModelForm, construct_instance, model_to_dict
from django.forms.widgets import HiddenInput, PasswordInput

from formset.collection import AddSiblingActivator, FormCollection
from formset.widgets import DualSelector, SelectizeMultiple

from testapp.models.user import User, ExtendUser, UserExtension


class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ['password', 'last_login', 'date_joined']
        widgets = {
            'password': PasswordInput,
            'groups': SelectizeMultiple,
            'user_permissions': DualSelector,
        }

    def is_valid(self):
        valid = super().is_valid()
        return valid


class UserContactForm(ModelForm):
    id = IntegerField(required=False, widget=HiddenInput)

    class Meta:
        model = ExtendUser
        fields = ['id', 'phone_number']

    def model_to_dict(self, main_object):
        try:
            opts = self._meta
            return model_to_dict(main_object.extend_user, fields=opts.fields)
        except ExtendUser.DoesNotExist:
            return {}

    def construct_instance(self, main_object):
        try:
            extend_user = main_object.extend_user
        except ExtendUser.DoesNotExist:
            extend_user = ExtendUser(user=main_object)
        form = UserContactForm(data=self.cleaned_data, instance=extend_user)
        if form.is_valid():
            construct_instance(form, extend_user)
            form.save()


class UserCollection(FormCollection):
    """
    Show how to combine multiple related forms into a single form collection.
    """
    user = UserForm()
    contact = UserContactForm()


class UserExtensionForm(ModelForm):
    id = IntegerField(required=False, widget=HiddenInput)

    class Meta:
        model = UserExtension
        fields = ['id', 'phone_number']


class UserListCollection(FormCollection):
    min_siblings = 0
    max_siblings = 4
    extra_siblings = 1
    induce_add_sibling = '.add_extension:active'
    extension = UserExtensionForm()
    add_label = "Add phone number"
    related_field = 'user'
    reverse_accessor = 'user_extensions'

    add_extension = AddSiblingActivator("Add phone number")

    def get_or_create_instance(self, data):
        if data := data.get('extension'):
            try:
                return self.instance.user_extensions.get(id=data.get('id') or 0), False
            except UserExtension.DoesNotExist:
                form = UserExtensionForm(data=data)
                if form.is_valid():
                    return UserExtension(phone_number=form.cleaned_data['phone_number'], user=self.instance), False
        return None, False


class UserExtensionCollection(FormCollection):
    user = UserForm()
    extensions = UserListCollection()
