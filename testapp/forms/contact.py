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

    A simple collection may look like:

    .. code-block:: python

        from formset.collection import FormCollection

        class PersonForm(forms.Form):
            last_name = fields.CharField(…)
            first_name = fields.CharField(…)

        class ProfessionForm(forms.Form):
            company = fields.CharField(…)
            job_title = fields.CharField(…, required=False)

        class SimpleContactCollection(FormCollection):
            person = PersonForm()
            profession = ProfessionForm()

    Such a collection behaves similar to a single form in the sense, that those two child
    forms, ``PersonForm`` and ``ProfessionForm``, are validated and submitted altogether.

    The dictionary with the submitted form data then contains two sub-dictionaries named
    ``person`` and ``profession``. Those sub-dictionaries then contain the form data for
    each form respectively.

    Such Collections can nest other Form Collections. This allows us to build hierarchies
    of forms with many nesting levels.
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
        r'^[01+][0-9 .-]+$',
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
    where the second form is wrapped into a *collection with siblings*. This allows us to
    submit siblings of the same form definition multiple times.

    Such a nested collection looks like:

    .. code-block:: python

        from formset.collection import FormCollection

        class PhoneNumberForm(forms.Form):
            phone_number = fields.RegexField(…)
            label = fields.ChoiceField(…)

        class PhoneNumberCollection(FormCollection):
            min_siblings = 1
            max_siblings = 5
            extra_siblings = 1

            number = PhoneNumberForm()

    The ``PhoneNumberCollection`` is a collection of another form, ie. ``PhoneNumberForm``,
    containg a phone number and a label field. That collection can contain up to five labeled
    phone numbers. Here the attributes ``min_siblings`` and ``max_siblings`` specify the minimum
    and maximum number of siblings for that collection. If ``max_siblings`` is unset or ``None``,
    an infinite number of siblings can be added. The attrinute ``extra_siblings`` specifies how
    many empty form collections shall be added.

    Finally, we glue those collections together:

    .. code-block:: python

        from formset.collection import FormCollection

        class PersonForm(forms.Form):
            last_name = fields.CharField(…)
            # … other fields

        class ContactCollection(FormCollection):
            legend = "Contact"
            person = PersonForm()
            numbers = PhoneNumberCollection()

    This gives us a nice form interface where we can add up to five phone numbers to each
    contact we have. Whenever we want to add a new sibling, we press onto the **+** symbol
    below the phone number collection. We can also delete siblings be clicking on the trash
    symbol, rendered while hovering over the corresponding phone number form.

    The framework always keeps track on the minimum and maximum number of siblings and
    wouldn't let us add or remove any sibling outside the allowed range.
    """
    legend = "Contact"
    # ignore_marked_for_removal = True

    person = PersonForm()

    numbers = PhoneNumberCollection()


class ContactCollectionList(FormCollection):
    """
    This Form Collection shows how to start right away as a *collection with siblings*. It can
    be used to create an editable list view of one or more forms.

    This collection is an extension of the previous example, where the outhermost collection
    is declared to allow siblings.

    .. code-block:: python

        from formset.collection import FormCollection

        class ContactCollectionList(FormCollection):
            legend = "List of Contacts"
            min_siblings = 0
            extra_siblings = 1

            person = PersonForm()
            numbers = PhoneNumberCollection(
                min_siblings=0,
                max_siblings=3,
                extra_siblings=0,
            )

    By passing in other values to the collection's constructor, we can respecify the
    number of mininimum, maximum and extra siblings.
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
    --------------------

    This is a variation of the ``ContactCollection`` demo, where we reuse the class
    ``PhoneNumberCollection``, and parametrize it be *sortable*. This allows the user to sort each
    child collection containing the phone number and label fields. The sorting can be performed by
    dragging the supplied drag handle in the top right corner of each sub collection.

    Declaring a ``FormCollection`` as sortable, is as simple as either adding the attribute
    ``is_sortable = True`` to the collection class or by instantiating the collection class
    as sortable. In this example we do the latter reusing the ``PhoneNumberCollection`` previously
    defined:

    .. code-block:: python

        from formset.collection import FormCollection
        from myproject.forms import PersonForm, PhoneNumberCollection

        class SortableContactCollection(FormCollection):
            person = PersonForm(initial={…})

            numbers = PhoneNumberCollection(
                max_siblings=5,
                is_sortable=True,
                initial=[…],
                help_text="A maximum of 5 phone numbers are allowed per contact.",
            )

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
    """
    This is a variation of the ``ContactCollectionList`` demo, which is parametrized to be sortable
    together with its sub form ``PhoneNumberCollection``. This allows the user to sort the outer
    collections separately from its inner collections, by using the supplied drag handle on the top
    right of each collection.

    Declaring a ``FormCollection`` as sortable, is as simple as either adding the attribute
    ``is_sortable = True`` to the collection class or by instantiating the collection class
    as sortable. By inheriting from ``ContactCollectionList`` we can add the attribute
    ``is_sortable`` to that class, while for its inner collections we reinstantiate it using
    ``PhoneNumberCollection(is_sortable=True)``.

    .. code-block:: python

        from myproject.forms import (ContactCollectionList,
                                     PhoneNumberCollection)

        class SortableContactCollectionList(ContactCollectionList):
            is_sortable = True

            numbers = PhoneNumberCollection(is_sortable=True)

    """

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
    -------------------------------------------------

    Here we wrap an existing FormCollection with siblings, into another FormCollection.
    Apart from adding an extra nesting level in the submitted data, this does not
    have any side effects.

    Using this might be useful if you want to add the legend and/or the help text outside the block
    containing the sortable collection of phone numbers.

    .. code-block:: python

        from formset.collection import FormCollection
        from myapp.forms import PersonForm

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
            legend = "List of Contacts"
            help_text = "Contacts can not be sorted, only their phone numbers."
            add_label = "Add new Contact"
            min_siblings = 0
            extra_siblings = 1

            person = PersonForm()

            intermediate = IntermediateCollection()
    """
    legend = "List of Contacts"
    help_text = "Contacts can not be sorted, only their phone numbers."
    add_label = "Add new Contact"
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    intermediate = IntermediateCollection()
