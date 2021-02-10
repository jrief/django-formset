import copy

from django.forms.utils import ErrorList
from django.utils.html import format_html, format_html_join, html_safe

from formset.boundfield import BoundField


@html_safe
class BootstrapErrorList(ErrorList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args and hasattr(args[0], 'client_messages'):
            self.client_messages = args[0].client_messages

    def copy(self):
        copy = super().copy()
        if hasattr(self, 'client_messages'):
            copy.client_messages = self.client_messages
        return copy

    def as_ul(self):
        lis = format_html_join('', '<li>{}</li>', ((e,) for e in self))
        if hasattr(self, 'client_messages'):
            return format_html(
                '<django-error-messages {}></django-error-messages><ul class="dj-errorlist"><li class="dj-placeholder"></li>{}</ul>',
                format_html_join(' ', '{0}="{1}"', ((key, value) for key, value in self.client_messages.items())), lis
            )
        return format_html('<ul class="dj-errorlist"><li class="dj-placeholder"></li>{}</ul>', lis)

    def __str__(self):
        return self.as_ul()


class BootstrapWidgetMixin:
    template_mapping = {
        'RadioSelect': 'formset/widgets/bootstrap4/radio.html',
        'CheckboxInput': 'formset/widgets/bootstrap4/checkbox.html',
        'CheckboxSelectMultiple': 'formset/widgets/bootstrap4/checkboxselectmultiple.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        class_name = self.__class__.__name__
        if class_name == 'CheckboxInput':
            context['checkbox_label'] = attrs.pop('checkbox_label')
        elif class_name in ['CheckboxSelectMultiple', 'RadioSelect']:
            inlined_checks = getattr(self, 'inlined_checks', None)
            if inlined_checks is None:
                # group all checkboxes into one line if there are less than 5
                max_options = 0
                for group, options, index in context['widget']['optgroups']:
                    if group is None:
                        max_options = len(context['widget']['optgroups'])
                        break
                    max_options = max(max_options, len(options))
                context['inlined_checks'] = max_options < 5
            else:
                context['inlined_checks'] = inlined_checks
        return context

    def render(self, name, value, attrs=None, renderer=None):
        # remap templates of widgets for Bootstrap
        template_name = self.template_mapping.get(self.__class__.__name__, self.template_name)
        context = self.get_context(name, value, attrs)
        return self._render(template_name, context, renderer)


class BootstrapFormMixin:
    field_css_classes = 'form-group'
    widget_css_classes = {
        'text': 'form-control',
        'email': 'form-control',
        'date': 'form-control',
        'select': 'form-control',
        'selectmultiple': 'form-control',
        'number': 'form-control',
        'textarea': 'form-control',
        'password': 'form-control',
    }

    def __init__(self, error_class=BootstrapErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def as_field_group(self):
        """
        Returns this form rendered as HTML similar to Bootstrap's Form Groups
        https://getbootstrap.com/docs/4.5/components/forms/#form-groups
        """
        # wrap non-field-errors into <div>-element to prevent re-boxing
        # error_row = self._error_row()
        control_css_classes = getattr(self, 'control_css_classes', None)
        if control_css_classes:
            normal_row = f'<django-field-group%(html_class_attr)s>%(label)s<div class="{control_css_classes}">%(field)s%(errors)s%(help_text)s</div></django-field-group>'
        else:
            normal_row = '<django-field-group%(html_class_attr)s>%(label)s%(field)s%(errors)s%(help_text)s</django-field-group>'
        html_element = self._html_output(
            normal_row=normal_row,
            error_row='<div class="dj-field-error">%s</div>',
            row_ender='</django-field-group>',
            help_text_html='<span class="form-text text-muted">%s</span>',
            errors_on_separate_row=False)
        return html_element

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field. In addition modify the widget class."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return BoundField(self, field, name)

    def get_widget(self, field):
        widget = copy.deepcopy(field.widget)
        widget.__class__ = type(widget.__class__.__name__, (BootstrapWidgetMixin, widget.__class__), {})
        return widget
