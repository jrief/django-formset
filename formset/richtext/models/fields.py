from django.db.models.fields.json import JSONField

from formset.richtext.widgets import RichTextarea


class RichTextField(JSONField):
    def formfield(self, **kwargs):
        form_field = super().formfield(**kwargs)
        if not isinstance(form_field.widget, RichTextarea):
            form_field.widget = RichTextarea()
        return form_field
