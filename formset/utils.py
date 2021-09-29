from django.forms.utils import ErrorList
from django.utils.html import format_html, format_html_join, html_safe
from django.utils.functional import cached_property

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


class FormMixin:
    def __init__(self, error_class=FormsetErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(f"Key {name} not found in Form")
        return BoundField(self, field, name)

    @cached_property
    def form_id(self):
        form_name = getattr(self, 'name', None)
        if form_name and self.auto_id and '%s' in str(self.auto_id):
            return self.auto_id % form_name

    def get_context(self):
        return {
            'form': self,
            'fields': [bf for bf in self.__iter__()],
        }
