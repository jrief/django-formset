from django.contrib.auth import get_user_model
from django.forms.fields import IntegerField
from django.forms.models import ModelForm, construct_instance, model_to_dict
from django.forms.widgets import HiddenInput, PasswordInput

from formset.collection import FormCollection
from formset.widgets import DualSelector, SelectizeMultiple

from testapp.models import ExtendUser, UserContact


class UserForm(ModelForm):
    class Meta:
        model = get_user_model()
        exclude = ['username', 'password', 'last_login', 'date_joined']
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

    def construct_instance(self, main_object, data):
        try:
            extend_user = main_object.extend_user
        except ExtendUser.DoesNotExist:
            extend_user = ExtendUser(user=main_object)
        form = UserContactForm(data=data, instance=extend_user)
        if form.is_valid():
            construct_instance(form, extend_user)
            form.save()


class UserCollection(FormCollection):
    user = UserForm()
    contact = UserContactForm()


class ContactsCollection(FormCollection):
    min_siblings = 0
    contact = UserContactForm()
    add_label = "Add phone number"

    def model_to_dict(self, user):
        opts = self.declared_holders['contact']._meta
        return [{'contact': model_to_dict(contact, fields=opts.fields)} for contact in user.contacts.all()]

    def construct_instance(self, user, data):
        for data in data:
            try:
                contact_object = user.contacts.get(id=data['contact']['id'])
            except (KeyError, UserContact.DoesNotExist):
                contact_object = UserContact(user=user)
            form_class = self.declared_holders['contact'].__class__
            form = form_class(data=data['contact'], instance=contact_object)
            if form.is_valid():
                if form.marked_for_removal:
                    contact_object.delete()
                else:
                    construct_instance(form, contact_object)
                    form.save()


class UserListCollection(FormCollection):
    user = UserForm()
    contacts = ContactsCollection()
