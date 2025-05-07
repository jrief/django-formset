from django.forms.fields import CharField, ChoiceField
from django.forms.forms import Form
from django.forms.widgets import RadioSelect

from formset.collection import FormCollection
from formset.dialog import ApplyButton, CancelButton, DialogForm
from formset.formfields.activator import Activator


class CoffeeForm(Form):
    nickname = CharField()
    add_flavor = Activator(
        label="Add flavor",
        help_text="Open the dialog to add a flavor",
    )


class FlavorForm(DialogForm):
    title = "Choose a Flavor"
    induce_open = '..coffee.add_flavor:active'
    induce_close = '.cancel:active || .apply:active'

    flavors = ChoiceField(
        choices=(
            ('caramel', "Caramel Macchiato"),
            ('cinnamon', "Cinnamon Dolce Latte"),
            ('hazelnut', "Turkish Hazelnut"),
            ('vanilla', "Vanilla Latte"),
            ('chocolate', "Chocolate Fudge"),
            ('almonds', "Roasted Almonds"),
            ('cream', "Irish Cream"),
        ),
        widget=RadioSelect,
        required=False,
    )
    cancel = Activator(
        label="Close",
        widget=CancelButton,
    )
    apply = Activator(
        label="Apply",
        widget=ApplyButton,
    )

class CoffeeOrderCollection(FormCollection):
    legend = "Order your coffee"
    coffee = CoffeeForm()
    flavor = FlavorForm()


class MultipleCoffeeOrderCollection(FormCollection):
    legend = "Order your coffee"
    add_label = "Add Coffee Order"
    min_siblings = 2
    extra_siblings = 1
    coffee = CoffeeForm()
    flavor = FlavorForm()


class CafeteriaCollection(FormCollection):
    coffee_order = MultipleCoffeeOrderCollection()
