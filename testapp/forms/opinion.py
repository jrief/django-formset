from django.forms import fields, forms, models, widgets

from formset.widgets import Selectize

from testapp.models import OpinionModel


class OpinionForm(forms.Form):
    choice = fields.ChoiceField(
        label="Classic Select",
        choices=[
            (None, "Commit yourself"),
            (1, "In favor"),
            (2, "Against"),
            (3, "Don't know"),
        ],
    )

    static_opinion = fields.ChoiceField(
        label="Static Opinion",
        choices=lambda: OpinionModel.objects.filter(tenant=1).values_list('id', 'label')[:500],
        widget = Selectize,
    )

    dynamic_opinion = models.ModelChoiceField(
        label="Dynamic Opinion",
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains', placeholder="Select my opinion"),
        required=True,
    )

    annotation = fields.CharField(
        label="Annotation",
        widget=widgets.TextInput(attrs={'placeholder': "Start typing ..."}),
        required=False,
        help_text="I have to say something",
    )


sample_opinion_data = {
    'choice': 2,
    'static_opinion': lambda: OpinionModel.objects.filter(tenant=1)[6],
    'dynamic_opinion': lambda: OpinionModel.objects.filter(tenant=1)[9],
    'annotation': "Lorem ipsum dolor est",
}
