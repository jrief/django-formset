from django.core.exceptions import ValidationError
from django.forms import fields, forms

from formset.collection import FormCollection
from formset.renderers.default import FormRenderer as DefaultFormRenderer

from .person import PersonForm


class ProfessionForm(forms.Form):
    company = fields.CharField(
        label="Company",
        min_length=2,
        max_length=50,
        help_text="The company's name",
    )

    job_title = fields.CharField(
        label="Job Title",
        max_length=50,
        required=False,
    )


class SimpleContactCollection(FormCollection):
    """
    A Form Collection can be used to combine two or more Django Forms into one collection.
    """

    person = PersonForm()

    profession = ProfessionForm()


class DefaultContactCollection(FormCollection):
    """
    Used to check, if the renderer can be overridden again.
    """
    person = PersonForm(renderer=DefaultFormRenderer())

    profession = ProfessionForm()


class PhoneNumberForm(forms.Form):
    phone_number = fields.RegexField(
        r'^[01+][ 0-9.\-]+$',
        label="Phone Number",
        min_length=2,
        max_length=20,
        help_text="Valid phone numbers start with + or 0 followed by digits and spaces",
    )

    label = fields.ChoiceField(
        label="Label",
        choices=[
            ('home', "Home"),
            ('work', "Work"),
            ('mobile', "Mobile"),
            ('other', "Other"),
        ],
    )

    def clean_phone_number(self):
        value = self.cleaned_data['phone_number'].replace(' ', '').replace('-', '').replace('.', '')
        if value == '+123456789':
            raise ValidationError("Are you kidding me?")
        return value


class PhoneNumberCollection(FormCollection):
    legend = "List of Phone Numbers"
    add_label = "Add new Phone Number"
    min_siblings = 1
    max_siblings = 5
    extra_siblings = 1

    number = PhoneNumberForm()


class ContactCollection(FormCollection):
    """
    This Form Collection shows how to combine two independend forms into one collection,
    where the second form is wrapped into a *collection with siblings*.
    """
    legend = "Contact"
    # ignore_marked_for_removal = True

    person = PersonForm()

    numbers = PhoneNumberCollection()


class ContactCollectionList(FormCollection):
    """
    This Form Collection shows how to start right away as a *collection with siblings*. It can
    be used to create an editable list view of one or more forms.
    """
    legend = "List of Contacts"
    add_label = "Add new Contact"
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=0,
        max_siblings=3,
        extra_siblings=0,
        is_sortable=True,
    )


class SortableContactCollection(FormCollection):
    """
    Sortable Collections
    """

    person = PersonForm(initial={
        'last_name': "Miller",
        'first_name': "Elisabeth",
    })

    numbers = PhoneNumberCollection(
        max_siblings=5,
        is_sortable=True,
        initial=[
            {'number': {'phone_number': "+1 234 567 8900"}},
            {'number': {'phone_number': "+39 335 327041"}},
            {'number': {'phone_number': "+41 91 667914"}},
            {'number': {'phone_number': "+49 89 7178864"}},
        ],
        help_text="A maximum of 5 phone numbers are allowed per contact.",
    )


class SortableContactCollectionList(ContactCollectionList):
    is_sortable = True

    numbers = PhoneNumberCollection(is_sortable=True)


class IntermediateCollection(FormCollection):
    help_text = "This intermediate collection adds another level of nesting without any benefit."

    numbers = PhoneNumberCollection(
        min_siblings=0,
        max_siblings=3,
        extra_siblings=0,
        is_sortable=True,
        help_text="Resort the phone numbers by using the drag handle on the upper right.",
    )


class IntermediateContactCollectionList(FormCollection):
    """
    Wrap a FormCollection into another FormCollection
    """
    legend = "List of Contacts"
    help_text = "Contacts can not be sorted, only their phone numbers."
    add_label = "Add new Contact"
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    intermediate = IntermediateCollection()
