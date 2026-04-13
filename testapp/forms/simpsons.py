from django.forms import fields, forms
from django.forms.widgets import TextInput


class SimpsonSelector(TextInput):
    template_name = 'testapp/simpsons-selector.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['is'] = 'simpsons-selector'
        context['widget']['simpsons'] = [
            ('abraham', "Abraham Simpson"),
            ('bart', "Bart Simpson"),
            ('burns', "Montgomery Burns"),
            ('flanders', "Ned Flanders"),
            ('lisa', "Lisa Simpson"),
            ('maggie', "Maggie Simpson"),
            ('marge', "Marge Simpson"),
            ('santas', "Santas Dog"),
        ]
        return context


class SimpsonsForm(forms.Form):
    member = fields.CharField(
        label="Member",
        initial="bart",
        widget=SimpsonSelector,
    )
