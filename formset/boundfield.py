from functools import lru_cache

from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile
from django.forms import boundfield
from django.forms.fields import FileField, JSONField
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from formset.formfields.activator import Activator
from formset.renderers import ClassList
from formset.upload import get_file_info
from formset.utils import FileFieldMixin
from formset.widgets import UploadedFileInput


class CheckboxInputMixin:
    """
    This special mixin is required for adding the field's label to the rendering context.
    This is to make the single checkbox to be rendered with its label after the input field.
    """
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['label'] = self.label
        return context


class BoundField(boundfield.BoundField):
    def __init__(self, form, field, name):
        if isinstance(field, FileField) and not isinstance(field, FileFieldMixin):
            # Fields of type ``FileField`` require a modified ``clean()``-method to handle Path objects
            field.__class__ = type(field.__class__.__name__, (FileFieldMixin, field.__class__), {})
        super().__init__(form, field, name)

    @property
    def errors(self):
        if isinstance(self.field, Activator):
            return ''  # submitted value of an Activator can not be validated, hence errors are not applicable
        errors = self.form.errors.get(self.name, self.form.error_class())
        errors.client_messages = self._get_client_messages()
        return errors

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        widget = widget or self.field.widget
        if self.widget_type == 'checkbox' and not isinstance(widget, CheckboxInputMixin):
            widget.__class__ = type(widget.__class__.__name__, (CheckboxInputMixin, widget.__class__), {'label': self.label})
        if self.field.localize:
            widget.is_localized = True
        attrs = attrs or {}
        attrs = self.build_widget_attrs(attrs, widget)
        if self.auto_id and 'id' not in widget.attrs:
            attrs.setdefault('id', self.html_initial_id if only_initial else self.auto_id)
        if isinstance(self.field, Activator) and self.name in ['submit', 'reset']:
            # A form control (such as a button) with a name of "submit" or "reset" will mask the form's internal
            # methods. This would cause a browser error. Please check the documentation for details:
            # https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/submit
            # https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/reset
            widget_name = f'activate_{self.name}'
        else:
            widget_name = self.name
        return widget.render(
            name=widget_name,  # `self.html_name` contains the full path and hence doesn't work with form collections
            value=self.value(),
            attrs=attrs,
            renderer=self.form.renderer,
        )

    def label_tag(self, **kwargs):
        if isinstance(self.field, Activator):
            return ''  # label of an Activator is placed inside its widget
        return super().label_tag(**kwargs)

    def css_classes(self, extra_classes=None):
        """
        Return a string of space-separated CSS classes for this field.
        """
        extra_classes = ClassList(extra_classes)
        if self.field.required:
            if self.widget_type == 'checkboxselectmultiple':
                extra_classes.add('dj-required-any')
            else:
                extra_classes.add('dj-required')

        # field_css_classes is an optional member of a FormRenderer optimized for django-formset
        field_css_classes = getattr(self.form.renderer, 'field_css_classes', None)
        if isinstance(field_css_classes, dict):
            try:
                extra_classes.add(field_css_classes[self.name])
            except KeyError:
                extra_classes.add(field_css_classes.get('*'))
        else:
            extra_classes.add(field_css_classes)
        return super().css_classes(extra_classes)

    def build_widget_attrs(self, attrs, widget=None):
        attrs = super().build_widget_attrs(attrs, widget)
        if hasattr(self.form, 'form_id'):
            attrs['form'] = self.form.form_id
        if hasattr(self.field, 'regex'):
            attrs['pattern'] = self.field.regex.pattern
        if isinstance(self.field, JSONField):
            attrs['use_json'] = True
        if isinstance(self.field, Activator) or self.widget_type == 'dualselector':
            label = self.name.replace('_', ' ').title() if self.field.label is None else self.field.label
            attrs['label'] = label  # remember label for ButtonWidget.get_context()
        return attrs

    @cached_property
    def widget_type(self):
        return super().widget_type

    @cached_property
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

    def value(self):
        value = super().value()
        if isinstance(value, FieldFile):
            return get_file_info(value)
        return value

    @lru_cache
    def _get_fieldset_info(self):
        fieldset = None
        parts = self.name.split('.')[:-1]
        declared_fieldsets = getattr(self.form, 'declared_fieldsets', {})
        for name in parts:
            if fieldset := declared_fieldsets.get(name):
                declared_fieldsets = fieldset.declared_fieldsets
            else:
                parts = []
                break
        return fieldset, '.'.join(parts)

    def as_fieldset(self):
        fieldset, fieldset_name = self._get_fieldset_info()
        return fieldset and fieldset_name != self.renderer._rendered_fields.get(self.name)

    def __str__(self):
        """Render this field as an HTML widget or as fieldset with widgets."""
        rendered_fieldset_name = self.renderer._rendered_fields.get(self.name)
        if rendered_fieldset_name is True:
            return ''  # field already rendered
        _, fieldset_name = self._get_fieldset_info()
        if (
            rendered_fieldset_name is None and fieldset_name or
            rendered_fieldset_name and rendered_fieldset_name != fieldset_name
        ):
            return self._render_fieldset()
        return super().__str__()

    def _render_fieldset(self):
        fieldset, fieldset_name = self._get_fieldset_info()
        field_names = [f'{fieldset_name}.{field_name}' for field_name in fieldset.declared_fields.keys()]
        context = fieldset.get_context()
        context.update(
            name=fieldset_name,
            fieldset=[self.form[field_name] for field_name in field_names],
        )
        self.renderer._rendered_fields.update({field_name: fieldset_name for field_name in field_names})
        rendered = self.renderer.render(fieldset.template_name, context)
        self.renderer._rendered_fields.update({field_name: True for field_name in field_names})
        return mark_safe(rendered)

    def _get_client_messages(self):
        """
        Extract server validation error messages to be rendered by the client side.
        """
        client_messages = {}
        server_messages = self.field.error_messages
        for validator in self.field.validators:
            validator_code = getattr(validator, 'code', None)
            if validator_code == 'invalid':
                client_messages['type_mismatch'] = client_messages['pattern_mismatch'] = validator.message
        if self.field.required is True:
            if self.widget_type == 'checkboxselectmultiple':
                client_messages['custom_error'] = _("At least one checkbox must be selected.")
            elif 'required' in server_messages:
                client_messages['value_missing'] = server_messages['required']
        if 'invalid' in server_messages:
            client_messages['type_mismatch'] = client_messages['pattern_mismatch'] = server_messages['invalid']
        elif 'invalid_choice' in server_messages:
            client_messages['type_mismatch'] = server_messages['invalid_choice']
        if 'bound_ordering' in server_messages:
            client_messages['custom_error'] = server_messages['bound_ordering']
        if getattr(self.field, 'max_length', None) is not None:
            data = {'max_length': self.field.max_length}
            max_length_message = _("Ensure this value has at most %(max_length)s characters.")
            if isinstance(self.field, FileField):
                client_messages['too_long'] = max_length_message % data
            else:
                client_messages['too_long'] = server_messages.get('max_length', max_length_message) % data
        if getattr(self.field, 'min_length', None) is not None:
            data = {'min_length': self.field.min_length}
            min_length_message = _("Ensure this value has at least %(min_length)s characters.")
            client_messages['too_short'] = server_messages.get('min_length', min_length_message) % data
        min_value = getattr(self.field, 'min_value', None)
        if min_value is not None or self.field.widget.attrs.get('min') is not None:
            if min_value is None:
                min_value = self.field.widget.attrs['min']
            data = {'limit_value': min_value() if callable(min_value) else min_value}
            client_messages['range_underflow'] = server_messages.get('min_value', validators.MinValueValidator.message) % data
        max_value = getattr(self.field, 'max_value', None)
        if max_value is not None or self.field.widget.attrs.get('max') is not None:
            if max_value is None:
                max_value = self.field.widget.attrs['max']
            data = {'limit_value': max_value() if callable(max_value) else max_value}
            client_messages['range_overflow'] = server_messages.get('max_value', validators.MaxValueValidator.message) % data
        try:
            step_value = float(self.field.widget.attrs['step'])
        except (KeyError, TypeError, ValueError):
            pass
        else:
            data = {'step_value': step_value}
            client_messages['step_mismatch'] = _("Input value must be a multiple of {step_value}.").format(**data)
        if self.widget_type == 'phonenumber':
            if self.field.widget.attrs.get('mobile-only'):
                client_messages['custom_error'] = _("Please enter a valid mobile number.")
            else:
                client_messages['custom_error'] = _("Please enter a valid phone number.")
        client_messages['bad_input'] = validators.ProhibitNullCharactersValidator.message
        if isinstance(self.field, FileField):
            if not isinstance(self.field.widget, UploadedFileInput):
                raise ImproperlyConfigured(
                    f"Field of type {self.field.__class__} must use widget inheriting from {UploadedFileInput}"
                )
            # abuse built-in client errors for failed file upload messages
            client_messages.update(
                type_mismatch=_("File upload still in progress."),
                bad_input=_("File upload failed."),
            )
        return client_messages
