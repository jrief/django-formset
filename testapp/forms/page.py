from django.forms.fields import CharField, SlugField
from django.forms.models import ModelChoiceField, ModelForm, construct_instance

from formset.collection import FormCollection
from formset.dialog import DialogModelForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button, Selectize, SlugInput

from testapp.models import Reporter, PageModel


class CreateReporterDialogForm(DialogModelForm):
    title = "Create Reporter"
    induce_open = 'page.add_reporter:active'
    induce_close = '.create:active || .cancel:active'
    cancel = Activator(
        label="Cancel",
        widget=Button(
            action='activate("close")',
            button_variant=ButtonVariant.SECONDARY,
        ),
    )
    create = Activator(
        label="Create Reporter",
        widget=Button(
            action='submitPartial -> setFieldValue(page.reporter, ^reporter_id) -> activate("clear")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = Reporter
        fields = ['full_name']

    def is_valid(self):
        if self.partial:
            return super().is_valid()
        self._errors = {}
        return True


class PageForm(ModelForm):
    title = CharField(
        label="Title",
        max_length=100,
    )
    slug = SlugField(
        label="Slug",
        required=False,
        widget=SlugInput(populate_from='title'),
    )
    reporter = ModelChoiceField(
        queryset=Reporter.objects.all(),
        label="Reporter",
        widget=Selectize(
            search_lookup='full_name__icontains',
        ),
        required=False,
    )
    add_reporter = Activator(
        label="Add Reporter",
        widget=Button(
            action='activate',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    class Meta:
        model = PageModel
        fields = ['title', 'slug', 'reporter']


class EditPageCollection(FormCollection):
    create_reporter = CreateReporterDialogForm()
    page = PageForm()

    def construct_instance(self, main_object):
        assert not self.partial
        instance = construct_instance(self.valid_holders['page'], main_object)
        instance.save()
        return instance
