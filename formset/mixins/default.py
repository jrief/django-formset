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
        list_items = format_html_join('', '<li>{}</li>', ((e,) for e in self))
        if hasattr(self, 'client_messages'):
            return format_html(
                '<django-error-messages {}></django-error-messages>' +
                '<ul class="dj-errorlist"><li class="dj-placeholder"></li>{}</ul>',
                format_html_join(' ', '{0}="{1}"', ((key, value) for key, value in self.client_messages.items())),
                list_items
            )
        return format_html('<ul class="dj-errorlist"><li class="dj-placeholder"></li>{}</ul>', list_items)

    def __str__(self):
        return self.as_ul()

    def __bool__(self):
        return True


class WidgetMixin:
    max_options_per_line = 5
    template_mapping = {
        'RadioSelect': 'formset/default/widgets/radio.html',
        'CheckboxSelectMultiple': 'formset/default/widgets/checkboxselectmultiple.html',
    }

    def get_context(self, name, value, attrs):
        context = {}
        class_name = self.__class__.__name__
        if class_name == 'CheckboxInput' and 'checkbox_label' in attrs:
            # some CSS frameworks require to wrap a single checkbox into a label
            context['checkbox_label'] = attrs.pop('checkbox_label')
        context.update(super().get_context(name, value, attrs))
        if class_name in ['CheckboxSelectMultiple', 'RadioSelect']:
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
    help_text_html = '<span class="dj-help-text">%s</span>'
    widget_mixin = WidgetMixin

    def __init__(self, error_class=FormsetErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def as_field_groups(self):
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
            error_row='<div class="dj-form-errors">%s</div>',
            row_ender='</django-field-group>',
            help_text_html=self.help_text_html,
            errors_on_separate_row=False)
        return mark_safe(strip_spaces_between_tags(html_element.strip()))

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field. In addition modify the widget class."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(f"Key {name} not found in Form")
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
        if css_classes:
            attrs['class'] = ' '.join(css_classes)

        # RegexField needs a modified context
        regex = getattr(bound_field.field, 'regex', None)
        if regex:
            attrs['pattern'] = regex.pattern

        return attrs

    def get_widget(self, field):
        widget = copy.deepcopy(field.widget)
        widget.__class__ = type(widget.__class__.__name__, (self.widget_mixin, widget.__class__), {})
        return widget


class CheckboxFormMixin:
    """
    Mixin class to let the checkbox widget render its label itself.
    """
    def get_widget_attrs(self, bound_field, attrs, widget):
        attrs = super().get_widget_attrs(bound_field, attrs, widget)

        # checkbox widgets render their label themselves
        if bound_field.widget_type == 'checkbox':
            attrs['checkbox_label'] = bound_field.label

        return attrs

    def render_label(self, bound_field, contents, attrs, label_suffix):
        label_css_classes = getattr(self, 'label_css_classes', None)
        if bound_field.widget_type == 'checkbox':
            checkbox_label_html = getattr(self, 'checkbox_label_html', None)
            if checkbox_label_html and label_css_classes:
                label_tag = format_html(checkbox_label_html, label_css_classes=label_css_classes)
            else:
                label_tag = ''
        else:
            if label_css_classes:
                attrs = dict(attrs or {})
                if 'class' in attrs:
                    attrs['class'] += ' ' + label_css_classes
                else:
                    attrs['class'] = label_css_classes
            label_tag = super().render_label(bound_field, contents, attrs, label_suffix)
        return label_tag
