from django.forms import fields, forms

from formset.collection import FormCollection
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
    add_label = "Add Accordion Item"
    ignore_marked_for_removal = True


class AccordionForm(ModelForm):
    """
    Form to show how to use ``CollectionField`` to map a JSONField.
    """
    context = CollectionField(AccordionCollection)

    class Meta:
        model = Component
        fields = ['context']
