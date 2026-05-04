from datetime import timedelta

from django.forms.fields import CharField, ChoiceField, DateTimeField, DecimalField, IntegerField
from django.forms.models import ModelForm, construct_instance
from django.forms.widgets import HiddenInput, Input, RadioSelect, TextInput, Textarea, URLInput, NumberInput
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from formset.collection import AddSiblingActivator, AddSiblingButton, FormCollection
from formset.formfields.activator import Activator
from formset.formfields.ranges import DateTimeRangeField
from formset.renderers import ButtonVariant
from formset.renderers.bootstrap import FormRenderer
from formset.richtext.dialogs import SimpleLinkDialogForm
from formset.widgets.richtext import RichTextarea, controls
from formset.stepper import StepperCollection
from formset.widgets import Button, DatePicker, DateTimeRangePicker, SlugInput, UploadedFileInput

from testapp.models.event import EventSeriesModel, EventOccurrenceModel


control_elements = [
    controls.Bold(),
    controls.Italic(),
    controls.BulletList(),
    controls.OrderedList(),
    controls.DialogControl(
        SimpleLinkDialogForm(),
        icon='formset/icons/link.svg',
    ),
    controls.Separator(),
    controls.ClearFormat(),
    controls.Undo(),
    controls.Redo(),
]


class EventSeriesForm(ModelForm):
    step_label = "General"
    default_renderer = FormRenderer(
        form_css_classes='row mb-3',
        field_css_classes={
            '*': 'mb-2 col-12',
        },
    )
    name = CharField(
        label="Name",
    )
    next = Activator(
        label="Occurrences",
        widget=Button(
            action='submitPartial({create_event: true}) -> setExtraData(event_id, ^event_id) -> activate("occurrences")',
            button_variant=ButtonVariant.SECONDARY,
            # attrs={'class': 'mt-3'},
        ),
    )

    class Meta:
        model = EventSeriesModel
        fields = [
            'name', 'slug', 'lead', 'image',
        ]
        widgets = {
            'slug': SlugInput('name'),
            'lead': RichTextarea(control_elements=control_elements, attrs={'maxlength': 500}),
            'image': UploadedFileInput(attrs={'accept': 'image/png, image/jpeg'}),
        }


class EmptyInput(HiddenInput):
    template_name = 'testapp/empty.html'


class EventOccurrenceForm(ModelForm):
    """
    Here we emulate a datetime range field by using a DateTimeRangeField that merges two DateTimeFields (begin, until)
    into one form field for better UX. Note that we have to override the `__init__`, `clean` and `get_initial_for_field`
    methods to split the values again.
    """

    # default_renderer = FormRenderer(
    #     form_css_classes='row mb-3',
    #     field_css_classes={
    #         '*': 'mb-2 col-12',
    #     },
    # )
    id = IntegerField(
        widget=HiddenInput,
        required=False,
    )
    begin_until = DateTimeRangeField(
        label=_("Begin- and end"),
        widget=DateTimeRangePicker(attrs={'step': timedelta(minutes=15), 'min': now().isoformat()}),
    )

    class Meta:
        model = EventOccurrenceModel
        fields = [
            'id', 'venue', 'begin', 'until',
        ]
        widgets = {
            'begin': EmptyInput(),
            'until': EmptyInput(),
        }

    def __init__(self, *args, **kwargs):
        self.base_fields['begin'].required = False
        self.base_fields['until'].required = False
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['begin'], cleaned_data['until'] = cleaned_data.get('begin_until', [None, None])
        return cleaned_data

    def get_initial_for_field(self, field, field_name):
        if field_name == 'begin_until' and self.instance:
            return self.initial.get('begin'), self.initial.get('until')
        return super().get_initial_for_field(field, field_name)


class EventOccurrenceCollection(FormCollection):
    step_label = "Event Occurrences"
    min_siblings = 1
    extra_siblings = 0
    event_occurrence = EventOccurrenceForm()
    default_renderer = FormRenderer()
    related_field = 'event_series'
    induce_activate = 'event_series.next:occurrences'
    induce_add_sibling = '.add_occurrence:add_sibling'

    add_occurrence = AddSiblingActivator(
        "Add Occurence",
        widget=AddSiblingButton(attrs={'class': 'd-block my-3'}),
    )
    next = Activator(
        label="About the Organizer",
        widget=Button(
            action='submitPartial({add_occurences: true}) -> setFieldValue(occurrences, ^occurrences) -> activate("organizer")',
            button_variant=ButtonVariant.SECONDARY,
            # attrs={'class': 'mt-3'},
        )
    )

    def get_or_create_instance(self, data, position):
        if data := data.get('event_occurrence'):
            try:
                return self.instance.occurrences.get(id=data.get('id') or 0), False
            except (AttributeError, EventOccurrenceModel.DoesNotExist, ValueError):
                form = EventOccurrenceForm(data=data)
                if form.is_valid():
                    return EventOccurrenceModel.objects.create(
                        event_series=self.instance,
                        venue=form.cleaned_data['venue'],
                        begin=form.cleaned_data['begin'],
                        until=form.cleaned_data['until'],
                    ), True
        return None, False


class EventOrganizerForm(ModelForm):
    # default_renderer = FormRenderer(
    #     form_css_classes='row mt-4',
    #     field_css_classes={
    #         '*': 'mb-2 col-12',
    #     },
    # )
    induce_activate = 'occurrences.next:organizer'
    step_label = "Event Organizer"

    # price = DecimalField(
    #     label=_("Eintrittspreis (€)"),
    #     widget=NumberInput(attrs={
    #         'df-show': '!.free_access',
    #         'df-require': '!.free_access',
    #         'step': '0.01',
    #         'min': '0',
    #     }),
    #     required=False,
    # )
    submit = Activator(
        label="Submit Event",
        widget=Button(
            action='clearErrors -> spinner -> submit -> okay(1500) -> proceed !~ scrollToError -> bummer(5000)',
            button_variant=ButtonVariant.PRIMARY,
            # attrs={'class': 'mt-3'},
        )
    )

    class Meta:
        model = EventSeriesModel
        fields = [
            'registration_deadline',
        ]
        widgets = {
            'registration_deadline': DatePicker(attrs={'min': now().date().isoformat()}),
        }


class EventSeriesCollection(StepperCollection):
    event_series = EventSeriesForm()
    occurrences = EventOccurrenceCollection()
    organizer = EventOrganizerForm()
