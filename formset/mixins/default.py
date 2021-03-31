import copy

from django.forms.utils import ErrorList
from django.utils.html import format_html, format_html_join, html_safe, strip_spaces_between_tags
from django.utils.safestring import mark_safe

from formset.boundfield import BoundField


@html_safe
class FormsetErrorList(ErrorList):
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


class WidgetMixin:
    max_options_per_line = 5
    template_mapping = {
        'RadioSelect': 'formset/widgets/default/radio.html',
        'CheckboxInput': 'formset/widgets/default/checkbox.html',
        'CheckboxSelectMultiple': 'formset/widgets/default/checkboxselectmultiple.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        class_name = self.__class__.__name__
        if class_name == 'CheckboxInput':
            context['checkbox_label'] = attrs.pop('checkbox_label', None)
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
                context['inlined_checks'] = max_options < self.max_options_per_line
            else:
                context['inlined_checks'] = inlined_checks
        return context

    def render(self, name, value, attrs=None, renderer=None):
        if not hasattr(self, 'template_name'):
            return super().render(name, value, attrs, renderer)
        # remap templates of widgets
        template_name = self.template_mapping.get(self.__class__.__name__, self.template_name)
        context = self.get_context(name, value, attrs)
        return self._render(template_name, context, renderer)


class FormMixin:
    help_text_html = '<span>%s</span>'

    def __init__(self, error_class=FormsetErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def as_field_group(self):
        """
        Returns this form rendered as HTML
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
            help_text_html=self.help_text_html,
            errors_on_separate_row=False)
        return mark_safe(strip_spaces_between_tags(html_element.strip()))

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field. In addition modify the widget class."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return BoundField(self, field, name)

    def render_label(self, bound_field, contents, attrs, label_suffix):
        return super(BoundField, bound_field).label_tag(contents, attrs, label_suffix)

    def get_widget_attrs(self, bound_field, attrs, widget):
        attrs = super(BoundField, bound_field).build_widget_attrs(attrs, widget)

        # widget_css_classes is an optional member of a Form optimized for django-formset
        css_classes = set(attrs.pop('class', '').split())
        widget_css_classes = getattr(self, 'widget_css_classes', None)
        if isinstance(widget_css_classes, dict):
            extra_css_classes = widget_css_classes.get(bound_field.widget_type)
            if isinstance(extra_css_classes, str):
                css_classes.add(extra_css_classes)
            elif isinstance(extra_css_classes, (list, tuple)):
                css_classes.update(extra_css_classes)
        attrs['class'] = ' '.join(css_classes)

        # some fields need a modified context
        regex = getattr(bound_field.field, 'regex', None)
        if regex:
            attrs['pattern'] = regex.pattern

        return attrs

    def get_widget(self, field):
        widget = copy.deepcopy(field.widget)
        widget.__class__ = type(widget.__class__.__name__, (WidgetMixin, widget.__class__), {})
        return widget
