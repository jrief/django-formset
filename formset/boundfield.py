from django.core import validators
from django.forms import boundfield
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _


class BoundField(boundfield.BoundField):
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

    def build_widget_attrs(self, attrs, widget=None):
        attrs = super().build_widget_attrs(attrs, widget)

        # widget_css_classes is an optional member of a Form optimized for django-formset
        css_classes = set(attrs.pop('class', '').split())
        widget_css_classes = getattr(self.form, 'widget_css_classes', None)
        if isinstance(widget_css_classes, dict):
            extra_css_classes = widget_css_classes.get(self.widget_type)
            if isinstance(extra_css_classes, str):
                css_classes.add(extra_css_classes)
            elif isinstance(extra_css_classes, (list, tuple)):
                css_classes.update(extra_css_classes)
        attrs['class'] = ' '.join(css_classes)

        # some fields need a modified context
        regex = getattr(self.field, 'regex', None)
        if regex:
            attrs['pattern'] = regex.pattern

        # checkbox widgets render their label themselves
        if self.widget_type == 'checkbox':
            attrs['checkbox_label'] = self.label

        return attrs

    @cached_property
    def widget_type(self):
        return super().widget_type

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        label_css_classes = getattr(self.form, 'label_css_classes', None)
        if self.widget_type == 'checkbox':
            if label_css_classes:
                label_tag = format_html('<div class="{}"></div>', label_css_classes)
            else:
                label_tag = ''
        else:
            if label_css_classes:
                attrs = dict(attrs or {})
                if 'class' in attrs:
                    attrs['class'] += ' ' + label_css_classes
                else:
                    attrs['class'] = label_css_classes
            label_tag = super().label_tag(contents, attrs, label_suffix)
        return label_tag

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        if widget is None:
            widget = self.form.get_widget(self.field)
        return super().as_widget(widget, attrs, only_initial)

    @property
    def errors(self):
        errors = self.form.errors.get(self.name, self.form.error_class())
        errors.client_messages = self.get_client_messages()
        return errors

    def get_client_messages(self):
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
            client_messages['too_long'] = _("Ensure this value has at most {max_length} characters.").format(**data)
        if getattr(self.field, 'min_length', None) is not None:
            data = {'min_length': self.field.min_length}
            client_messages['too_short'] = _("Ensure this value has at least {min_length} characters.").format(**data)
        if getattr(self.field, 'min_value', None) is not None:
            data = {'limit_value': self.field.min_value}
            client_messages['range_underflow'] = validators.MinValueValidator.message % data
        if getattr(self.field, 'max_value', None) is not None:
            data = {'limit_value': self.field.max_value}
            client_messages['range_overflow'] = validators.MaxValueValidator.message % data
        try:
            step_value = float(self.field.widget.attrs['step'])
        except (KeyError, TypeError):
            pass
        else:
            data = {'step_value': step_value}
            client_messages['step_mismatch'] = _("Input value must be a multiple of {step_value}").format(**data)
        client_messages['bad_input'] = validators.ProhibitNullCharactersValidator.message
        return client_messages
