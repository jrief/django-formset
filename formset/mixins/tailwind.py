from formset.mixins.default import FormMixin


class TailwindFormMixin(FormMixin):
    """
    Class to mix into a Django ``Form`` or ``ModelForm`` class.

    Adopt styles by editing assets/tailwind-styles.css and recompile using:
    ``npm run tailwindcss``
    """
    field_css_classes = 'mb-6'
    help_text_html='<p class="formset-help-text">%s</p>'
    widget_css_classes = {
        'text': 'formset-text-input',
        'email': 'formset-email-input',
        'date': 'formset-date-input',
        'checkbox': 'formset-checkbox',
        'checkboxselectmultiple': 'formset-checkbox-multiple',
        'radioselect': 'formset-radio-select',
        'select': 'formset-select',
        'selectmultiple': 'formset-select-multiple',
        'number': 'formset-number-input',
        'textarea': 'formset-textarea',
        'password': 'formset-password-input',
    }
