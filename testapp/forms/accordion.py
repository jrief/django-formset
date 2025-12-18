from django.forms import fields, forms

from formset.collection import AddSiblingActivator, FormCollection
from formset.formfields.collection import CollectionField
from formset.formfields.richtext import RichTextField
from formset.forms import ModelForm

from testapp.models.component import Component


class AccordionItem(forms.Form):
    heading = fields.CharField(
        label="Accordion Heading",
        max_length=100,
    )
    body = RichTextField(
        label="Accordion Body",
        required=False,
    )


class AccordionCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 0
    accordion_item = AccordionItem()
    legend = "Accordion"
    induce_add_sibling = '.add_item:active'
    ignore_marked_for_removal = True

    add_item = AddSiblingActivator("Add Accordion Item")


class AccordionForm(ModelForm):
    """
    Form to show how to use ``CollectionField`` to map a JSONField.
    """
    context = CollectionField(AccordionCollection)

    class Meta:
        model = Component
        fields = ['context']
