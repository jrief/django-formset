from django.forms.fields import CharField, IntegerField
from django.forms.models import ModelChoiceField, ModelForm, ModelMultipleChoiceField, construct_instance
from django.forms.widgets import HiddenInput

from formset.collection import FormCollection
from formset.dialog import DialogModelForm
from formset.formfields.activator import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button, DualSelector, Selectize, SelectizeMultiple

from testapp.models import Reporter, IssueModel


class ChangeReporterDialogForm(DialogModelForm):
    cancel = Activator(
        label="Cancel",
        widget=Button(
            action='activate("close")',
            button_variant=ButtonVariant.SECONDARY,
        ),
    )

    def is_valid(self):
        if self.partial:
            return super().is_valid()
        self._errors = {}
        return True


class EditReporterDialogForm(ChangeReporterDialogForm):
    title = "Edit Reporter"
    induce_open = 'issue.edit_reporter:active'
    induce_close = '.change:active || .cancel:active'

    id = IntegerField(widget=HiddenInput)
    change = Activator(
        label="Change Reporter",
        widget=Button(
            action='submitPartial -> setFieldValue(issue.reporter, ^reporter_id) -> activate("clear")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = Reporter
        fields = ['id', 'full_name']


class CreateReporterDialogForm(ChangeReporterDialogForm):
    title = "Create Reporter"
    induce_open = 'issue.add_reporter:active'
    induce_close = '.create:active || .cancel:active'

    create = Activator(
        label="Create Reporter",
        widget=Button(
            action='submitPartial -> setFieldValue(issue.reporter, ^reporter_id) -> activate("clear")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = Reporter
        fields = ['full_name']


class IssueSingleForm(ModelForm):
    title = CharField(
        label="Title",
        max_length=100,
    )
    reporter = ModelChoiceField(
        queryset=Reporter.objects.all(),
        label="Reporter",
        widget=Selectize(
            search_lookup='full_name__icontains',
        ),
        required=True,
    )
    edit_reporter = Activator(
        label="Edit Reporter",
        widget=Button(
            action='activate(prefillPartial(issue.reporter))',
            attrs={'df-disable': '!issue.reporter'},
            button_variant=ButtonVariant.SUCCESS,
        ),
    )
    add_reporter = Activator(
        label="Add Reporter",
        widget=Button(
            action='activate',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = IssueModel
        fields = ['title', 'reporter']


class CreateReporterManyDialogForm(CreateReporterDialogForm):
    create = Activator(
        label="Create Reporter",
        widget=Button(
            action='submitPartial -> setFieldValue(issue.reporters, ^reporter_id) -> activate("clear")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )


class IssueManyForm(ModelForm):
    title = CharField(
        label="Title",
        max_length=100,
    )
    reporters = ModelMultipleChoiceField(
        queryset=Reporter.objects.all(),
        label="Reporters",
        widget=SelectizeMultiple(
            search_lookup='full_name__icontains',
        ),
        required=True,
    )
    add_reporter = Activator(
        label="Add Reporter",
        widget=Button(
            action='activate',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = IssueModel
        fields = ['title', 'reporters']


class EditIssueCollection(FormCollection):
    create_reporter = CreateReporterDialogForm()
    edit_reporter = EditReporterDialogForm()
    issue = IssueSingleForm()

    def construct_instance(self, main_object):
        assert not self.partial
        instance = construct_instance(self.valid_holders['issue'], main_object, fields=['title', 'reporter'])
        instance.save()
        return instance


class EditIssueManyCollection(FormCollection):
    create_reporter = CreateReporterManyDialogForm()
    issue = IssueManyForm()

    def construct_instance(self, main_object):
        assert not self.partial
        instance = construct_instance(self.valid_holders['issue'], main_object, fields=['title'])
        self.valid_holders['issue'].instance = instance
        self.valid_holders['issue'].save()  # this also saves field `reporters` (many-to-many)
        return instance
