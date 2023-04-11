from django.forms.fields import CharField
from django.forms.forms import Form
from django.views.generic import FormView


class PersonForm(Form):
    first_name = CharField()
    last_name = CharField()


class DemoFormView(FormView):
    form_class = PersonForm
    template_name = 'docs/extended-form.html'
