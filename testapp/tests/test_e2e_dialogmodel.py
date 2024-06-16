import pytest
from time import sleep
from playwright.sync_api import expect

from django.urls import path
from django.forms.fields import CharField, IntegerField
from django.forms.models import ModelChoiceField, ModelForm, construct_instance
from django.forms.widgets import HiddenInput
from django.http import JsonResponse, HttpResponseBadRequest

from formset.collection import FormCollection
from formset.dialog import DialogModelForm
from formset.fields import Activator
from formset.views import EditCollectionView
from formset.widgets import Button, Selectize

from .utils import get_javascript_catalog

from testapp.models import Reporter, IssueModel


class ChangeReporterDialogForm(DialogModelForm):
    title = "Edit Reporter"
    induce_open = 'issue.edit_reporter:active || issue.add_reporter:active'
    induce_close = '.change:active || .cancel:active'

    id = IntegerField(
        widget=HiddenInput,
        required=False,
        help_text="Primary key of Reporter object. Leave empty to create a new object.",
    )
    cancel = Activator(
        widget=Button(action='activate("close")'),
    )
    change = Activator(
        widget=Button(
            action='submitPartial -> setFieldValue(issue.reporter, ^reporter_id) -> activate("clear")',
        ),
    )

    class Meta:
        model = Reporter
        fields = ['id', 'full_name']

    def is_valid(self):
        if self.partial:
            return super().is_valid()
        self._errors = {}
        return True


class IssueForm(ModelForm):
    title = CharField()
    reporter = ModelChoiceField(
        queryset=Reporter.objects.all(),
        widget=Selectize(
            search_lookup='full_name__icontains',
        ),
    )
    edit_reporter = Activator(
        widget=Button(
            action='activate(prefillPartial(issue.reporter))',
            attrs={'df-disable': '!issue.reporter'},
        ),
    )
    add_reporter = Activator(
        widget=Button(
            action='activate',
        ),
    )
    delete_reporter = Activator(
        widget=Button(
            action='deletePartial(change_reporter, issue.reporter) -> setFieldValue(issue.reporter, "")',
            attrs={'df-disable': '!issue.reporter'},
        ),
    )

    class Meta:
        model = IssueModel
        fields = ['title', 'reporter']


class EditIssueCollection(FormCollection):
    change_reporter = ChangeReporterDialogForm()
    issue = IssueForm()

    def construct_instance(self, main_object):
        assert not self.partial
        instance = construct_instance(self.valid_holders['issue'], main_object)
        instance.save()
        return instance


class IssueCollectionView(EditCollectionView):
    model = IssueModel
    collection_class = EditIssueCollection
    template_name = 'testapp/form-collection.html'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.last()

    def form_collection_valid(self, form_collection):
        if form_collection.partial:
            if not (valid_holder := form_collection.valid_holders.get('change_reporter')):
                return HttpResponseBadRequest("Form data is missing.")
            if id := valid_holder.cleaned_data['id']:
                reporter = Reporter.objects.get(id=id)
                construct_instance(valid_holder, reporter)
            else:
                reporter = construct_instance(valid_holder, Reporter())
            reporter.save()
            return JsonResponse({'reporter_id': reporter.id})
        return super().form_collection_valid(form_collection)


urlpatterns = [
    path('issue', IssueCollectionView.as_view(
        collection_class=EditIssueCollection,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='issue'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['issue'])
def test_add_reporter(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(0).locator('> dialog')
    expect(dialog).not_to_be_visible()
    select_reporter = form_collection.locator('select[name="reporter"]')
    expect(select_reporter).to_have_value('')
    Reporter.objects.filter(full_name="Sarah Hemingway").delete()

    # open the dialog and add a new reporter
    form_collection.nth(1).locator('button[name="add_reporter"]').click()
    expect(dialog).to_be_visible()
    dialog.locator('button[name="change"]').click()
    full_name_input = dialog.locator('input[name="full_name"]')
    expect(full_name_input.locator('+ [role="alert"]')).to_have_text("This field is required.")
    expect(dialog.locator('> div.dialog-header > h3')).to_have_text("Edit Reporter")
    full_name_input.fill("Sarah Hemingway")
    expect(full_name_input.locator('+ [role="alert"]')).to_be_empty()
    full_name_input.blur()
    spy = mocker.spy(IssueCollectionView, 'post')
    dialog.locator('button[name="change"]').click()
    expect(dialog).not_to_be_visible()

    # check if the reporter was added to main form
    sleep(0.25)
    spy.assert_called()
    reporter = Reporter.objects.get(full_name="Sarah Hemingway")
    expect(select_reporter).to_have_value(str(reporter.id))
    pseudo_input = form_collection.nth(1).locator(f'.ts-wrapper div.item[data-value=\"{reporter.id}\"]')
    expect(pseudo_input).to_have_text("Sarah Hemingway")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['issue'])
def test_edit_reporter(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(0).locator('> dialog')
    expect(dialog).not_to_be_visible()
    select_reporter = form_collection.locator('select[name="reporter"]')
    expect(select_reporter).to_have_value('')
    reporter, _ = Reporter.objects.get_or_create(full_name="Sarah Hemingway")
    select_reporter.evaluate(f'el => el.value = {reporter.id}')
    expect(select_reporter).to_have_value(str(reporter.id))
    pseudo_input = form_collection.nth(1).locator(f'.ts-wrapper div.item[data-value=\"{reporter.id}\"]')
    expect(pseudo_input).to_have_text("Sarah Hemingway")

    # open the dialog and edit the current reporter
    form_collection.nth(1).locator('button[name="edit_reporter"]').click()
    expect(dialog).to_be_visible()
    full_name_input = dialog.locator('input[name="full_name"]')
    expect(full_name_input).to_have_value("Sarah Hemingway")
    expect(dialog.locator('> div.dialog-header > h3')).to_have_text("Edit Reporter")
    full_name_input.fill("Sarah Johnson")
    full_name_input.blur()
    spy = mocker.spy(IssueCollectionView, 'post')
    dialog.locator('button[name="change"]').click()
    expect(dialog).not_to_be_visible()

    # check if the reporter was changed on the main form
    sleep(0.25)
    spy.assert_called()
    assert Reporter.objects.get(id=reporter.id).full_name == "Sarah Johnson"
    expect(select_reporter).to_have_value(str(reporter.id))
    expect(pseudo_input).to_have_text("Sarah Johnson")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['issue'])
def test_delete_reporter(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    dialog = form_collection.nth(0).locator('> dialog')
    expect(dialog).not_to_be_visible()
    select_reporter = form_collection.locator('select[name="reporter"]')
    expect(select_reporter).to_have_value('')
    reporter, _ = Reporter.objects.get_or_create(full_name="Sarah Hemingway")
    select_reporter.evaluate(f'el => el.value = {reporter.id}')
    expect(select_reporter).to_have_value(str(reporter.id))
    pseudo_input = form_collection.nth(1).locator(f'.ts-wrapper div.item[data-value=\"{reporter.id}\"]')
    expect(pseudo_input).to_have_text("Sarah Hemingway")

    # delete the current reporter remotely
    spy = mocker.spy(IssueCollectionView, 'delete')
    form_collection.nth(1).locator('button[name="delete_reporter"]').click()

    # check if the reporter was deleted from the database and from the selectize widget
    sleep(1)
    spy.assert_called()
    assert not Reporter.objects.filter(id=reporter.id).exists()
    expect(select_reporter).to_have_value('')
    expect(pseudo_input).not_to_be_visible()
