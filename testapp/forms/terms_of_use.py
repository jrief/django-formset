from django.forms import fields, forms, widgets
from django.utils.safestring import mark_safe

from formset.collection import FormCollection
from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button


class AcceptDialogForm(DialogForm):
    title = "Terms of Use"
    prologue = mark_safe("""
        <p>This site does not allow content or activity that:</p>
        <ul>
            <li>is unlawful or promotes violence.</li>
            <li>shows sexual exploitation or abuse.</li>
            <li>harasses, defames or defrauds other users.</li>
            <li>is discriminatory against other groups of users.</li>
            <li>violates the privacy of other users.</li>
        </ul>
        <p><strong>Before proceeding, please accept the terms of use.</strong></p>
    """)
    induce_open = 'submit:active'
    induce_close = '.accept:active || .deny:active'
    accept = Activator(
        label="Accept",
        widget=Button(
            action='setFieldValue(user.accept_terms, true) -> activate("close")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )
    deny = Activator(
        label="Deny",
        widget=Button(
            action='activate("close")',
            button_variant=ButtonVariant.SECONDARY,
        ),
    )


class UserNameForm(forms.Form):
    full_name = fields.CharField(
        label="Full Name",
        max_length=100,
    )
    accept_terms = fields.BooleanField(
        required=False,
        widget=widgets.HiddenInput,
    )


class AcceptTermsCollection(FormCollection):
    legend = "User Acceptance Collection"
    user = UserNameForm()
    accept = AcceptDialogForm(is_modal=True)
    submit = Activator(
        label="Submit",
        widget=Button(
            action='user.accept_terms ? disable -> submit -> reload !~ scrollToError : activate',
            button_variant=ButtonVariant.PRIMARY,
            icon_path='formset/icons/send.svg',
        ),
    )
    reset = Activator(
        label="Reset to initial",
        widget=Button(
            action='reset',
            button_variant=ButtonVariant.WARNING,
            icon_path='formset/icons/reset.svg',
        ),
    )
