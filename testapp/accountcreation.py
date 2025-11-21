from formset.collection import FormCollection
from formset.stepper import StepperCollection
from formset.forms import Form as FormsetForm
from formset.dialog import DialogForm
from formset.formfields.activator import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button, DateTextbox

class AcceptDialogForm(DialogForm):
    title = "Terms of Use"
    epilogue = mark_safe(
        """
        <p>This site does not allow content or activity that:</p>
        <ul>
            <li>is unlawful or promotes violence.</li>
            <li>shows sexual exploitation or abuse.</li>
            <li>harasses, defames or defrauds other users.</li>
            <li>is discriminatory against other groups of users.</li>
            <li>violates the privacy of other users.</li>
        </ul>
        <p><strong>Before proceeding, please accept the terms of use.</strong></p>
    """
    )
    induce_open = "stepper.step_three.open_terms_modal:active || stepper.step_three.submit:active || stepper.step_three.submit_activator:active"
    induce_close = ".accept:active || .reject:active"
    accept = Activator(
        label="Accept",
        widget=Button(
            action='setFieldValue(stepper.step_three.accept_terms, "on") -> activate("close")',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )
    reject = Activator(
        label="Reject",
        widget=Button(
            action='activate("close")',
            button_variant=ButtonVariant.SECONDARY,
        ),
    )


class AccountRegistrationContactForm(FormsetForm):
    """Collect contact details for initial account registration."""

    step_label = "Contact"
    induce_activate = None  # first step, no induction needed
    registration_id = IntegerField(required=False, widget=forms.HiddenInput)
    email = EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    birthday = DateField(
        label="Birthday",
        widget=DateTextbox,
    )
    next = Activator(
        label="Next",
        widget=Button(
            action='submitPartial -> setFieldValue(stepper.step_one.registration_id, ^registration_id) -> setFieldValue(stepper.step_two.registration_id, ^registration_id) -> setFieldValue(stepper.step_two.email, stepper.step_one.email) -> setFieldValue(stepper.step_three.registration_id, ^registration_id) -> activate("apply")'
        ),
    )


class AccountRegistrationVerificationForm(FormsetForm):

    step_label = "Verify Email"
    induce_activate = "stepper.step_one.next:active"

    # Hidden field to track partial updates
    registration_id = IntegerField(required=False, widget=forms.HiddenInput)
    # Hidden field to track email for use in the resend activator
    email = EmailField(required=False, widget=forms.HiddenInput)

    verification_code = CharField(
        label="Email Verification Code",
        help_text="A verification code has been emailed to you.",
        max_length=6,
        validators=[RegexValidator(r"^\d{6}$", _("Enter the 6-digit code we sent you."))],
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "placeholder": "Enter 6-digit code",
            }
        ),
    )

    resend_email = Activator(
        label="Resend Email",
        widget=Button(
            action='emit("account-registration:verify-email-resend")',
            attrs={
                "data-forward-fields": "registration_id email",
            },
        ),
    )

    next = Activator(label="Next", widget=Button(action='submitPartial -> activate("apply")'))


class AccountRegistrationCredentialsForm(FormsetForm):
    """Collect username, password, and consent to terms."""

    step_label = "Credentials"
    induce_activate = "stepper.step_two.next:active"

    # Hidden field to track partial updates
    registration_id = IntegerField(required=False, widget=forms.HiddenInput)

    username = CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(),
    )
    password = CharField(
        label="Password",
        min_length=8,
        max_length=20,
        widget=forms.PasswordInput(),
        help_text="Between 8 and 20 characters.",
    )
    accept_terms = BooleanField(
        label="I agree to the placeholder terms and conditions.",
        initial="",
        required=True,
    )
    # dedicated activator to open the terms modal
    open_terms_modal = Activator(
        label="terms of use",
        widget=Button(
            action="activate",
        ),
    )
    # invoking activate wont work because "submit" is a reserved/blessed word
    submit = Activator(
        label="Submit",
        widget=Button(
            action='stepper.step_three.accept_terms == "" ? activate : submit -> proceed',
        ),
    )
    # invoking activate will work because submit_activator is a custom name
    submit_activator = Activator(
        label="Submit",
        widget=Button(
            action='stepper.step_three.accept_terms == "" ? activate : submit -> proceed',
        ),
    )


class AccountRegistrationStepper(StepperCollection):
    """Stepper wiring for progressive account registration."""

    template_name = "custom_widget_templates/custom_stepper_collection_no_banner.html"

    step_one = AccountRegistrationContactForm()

    step_two = AccountRegistrationVerificationForm()

    step_three = AccountRegistrationCredentialsForm()


class AccountRegistrationCollection(FormCollection):
    """
    Parent collection that holds:
      - The stepper (its own internal steps)
      - The terms dialog as a sibling (NOT a step)
    """

    legend = "Create Your StoryArk Account"

    stepper = AccountRegistrationStepper()
    terms = AcceptDialogForm(is_modal=True)  # on step three
