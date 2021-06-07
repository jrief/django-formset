from django.core import validators
from django.forms import boundfield
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from formset.widgets import UploadedFileInput


class BoundField(boundfield.BoundField):
    @property
    def errors(self):
        errors = self.form.errors.get(self.name, self.form.error_class())
        errors.client_messages = self._get_client_messages()
        return errors

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        if widget is None:
            widget = self.form.get_widget(self.field)
        return super().as_widget(widget, attrs, only_initial)

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        return self.form.render_label(self, contents, attrs, label_suffix)

    def css_classes(self, extra_classes=None):
        """
        Return a string of space-separated CSS classes for this field.
        """
        if hasattr(extra_classes, 'split'):
            extra_classes = extra_classes.split()
        extra_classes = set(extra_classes or [])
        if self.field.required:
            if self.widget_type == 'checkboxselectmultiple':
                extra_classes.add('dj-required-any')
            else:
                extra_classes.add('dj-required')

        # field_css_classes is an optional member of a Form optimized for django-formset
        field_css_classes = getattr(self.form, 'field_css_classes', None)
        if hasattr(field_css_classes, 'split'):
            extra_classes.update(field_css_classes.split())
        elif isinstance(field_css_classes, (list, tuple)):
            extra_classes.update(field_css_classes)
        return super().css_classes(extra_classes)

    @cached_property
    def widget_type(self):
        return super().widget_type

    @property
    def auto_id(self):
        """
        Since we can have many forms with a different name each, prefix the id with the form name
        """
        auto_id = self.form.auto_id
        if auto_id and '%s' in str(auto_id):
            auto_id = auto_id % self.html_name
            if getattr(self.form, 'name', None):
                return f'{self.form.name}_{auto_id}'
            return auto_id
        elif auto_id:
            return self.html_name
        return ''

    def build_widget_attrs(self, attrs, widget=None):
        return self.form.get_widget_attrs(self, attrs, widget)

    def _get_client_messages(self):
        """
        Extract server validation error messages to be rendered by the client side.
        """
        client_messages = {}
        server_messages = self.field.error_messages
        if self.field.required is True:
            if self.widget_type == 'checkboxselectmultiple':
                client_messages['custom_error'] = _("At least one checkbox must be selected.")
            elif 'required' in server_messages:
                client_messages['value_missing'] = server_messages['required']
        if 'invalid' in server_messages:
            client_messages['type_mismatch'] = client_messages['pattern_mismatch'] = server_messages['invalid']
        elif 'invalid_choice' in server_messages:
            client_messages['type_mismatch'] = server_messages['invalid_choice']
        else:
            for validator in self.field.validators:
                validator_code = getattr(validator, 'code', None)
                if validator_code == 'invalid':
                    client_messages['type_mismatch'] = validator.message
        if getattr(self.field, 'max_length', None) is not None:
            data = {'max_length': self.field.max_length}
            max_length_message = _("Ensure this value has at most %(max_length)s characters.")
            client_messages['too_long'] = server_messages.get('max_length', max_length_message) % data
        if getattr(self.field, 'min_length', None) is not None:
            data = {'min_length': self.field.min_length}
            min_length_message = _("Ensure this value has at least %(min_length)s characters.")
            client_messages['too_short'] = server_messages.get('min_length', min_length_message) % data
        if getattr(self.field, 'min_value', None) is not None:
            data = {'limit_value': self.field.min_value}
            client_messages['range_underflow'] = server_messages.get('min_value', validators.MinValueValidator.message) % data
        if getattr(self.field, 'max_value', None) is not None:
            data = {'limit_value': self.field.max_value}
            client_messages['range_overflow'] = server_messages.get('max_value', validators.MaxValueValidator.message) % data
        try:
            step_value = float(self.field.widget.attrs['step'])
        except (KeyError, TypeError):
            pass
        else:
            data = {'step_value': step_value}
            client_messages['step_mismatch'] = _("Input value must be a multiple of {step_value}.").format(**data)
        client_messages['bad_input'] = validators.ProhibitNullCharactersValidator.message
        if isinstance(self.field.widget, UploadedFileInput):
            # abuse built-in client errors for failed file upload messages
            client_messages.update(
                type_mismatch=_("File upload still in progress."),
                bad_input=_("File upload failed."),
            )
        return client_messages
