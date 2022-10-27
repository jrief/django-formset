from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile
from django.forms import boundfield
from django.forms.fields import FileField, JSONField
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from formset.upload import get_file_info
from formset.widgets import UploadedFileInput


class ClassList(set):
    """
    Inspired by JavaScript's classlist on HTMLElement
    """
    __slots__ = ()

    def __init__(self, css_classes=None):
        if css_classes is None:
            super().__init__()
        elif isinstance(css_classes, (list, set, tuple)):
            super().__init__(css_classes)
        elif isinstance(css_classes, str):
            super().__init__(css_classes.split())
        else:
            raise TypeError(f"Can not convert {css_classes.__class__} to ClassList")

    def __bool__(self):
        return len(self) > 0

    def add(self, css_classes):
        for css_class in ClassList(css_classes):
            super().add(css_class)
        return self

    def remove(self, css_classes):
        for css_class in ClassList(css_classes):
            if css_class in self:
                super().remove(css_class)
        return self

    def toggle(self, css_classes, condition=None):
        for css_class in ClassList(css_classes):
            if css_class in self:
                if condition in (None, False):
                    super().remove(css_class)
            else:
                if condition in (None, True):
                    super().add(css_class)
        return self

    def render(self):
        return ' '.join(self)

    __str__ = render
    __html__ = render


class CheckboxInputMixin:
    """
    This hack is required for adding the field's label to the rendering context.
    This is to make the single checkbox to be rendered with its label after the input field.
    """
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['label'] = self.label
        return context


class BoundField(boundfield.BoundField):
    @property
    def errors(self):
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
        return widget.render(
            name=self.name,  # `self.html_name` contains the full path and hence doesn't work with form collections
            value=self.value(),
            attrs=attrs,
            renderer=self.form.renderer,
        )

    def build_widget_attrs(self, attrs, widget=None):
        attrs = super().build_widget_attrs(attrs, widget)
        if hasattr(self.form, 'form_id'):
            attrs['form'] = self.form.form_id
        if hasattr(self.field, 'regex'):
            attrs['pattern'] = self.field.regex.pattern
        if isinstance(self.field, JSONField):
            attrs['use_json'] = True
        return attrs

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
                if self.widget_type == 'selectize':
                    client_messages['custom_error'] = server_messages['required']
                else:
                    client_messages['value_missing'] = server_messages['required']
        if 'invalid' in server_messages:
            client_messages['type_mismatch'] = client_messages['pattern_mismatch'] = server_messages['invalid']
        elif 'invalid_choice' in server_messages:
            client_messages['type_mismatch'] = server_messages['invalid_choice']
        else:
            for validator in self.field.validators:
                validator_code = getattr(validator, 'code', None)
                if validator_code == 'invalid':
                    client_messages['type_mismatch'] = client_messages['pattern_mismatch'] = validator.message
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
