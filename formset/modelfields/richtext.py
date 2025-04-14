from django.db.models.fields.json import JSONField

from formset.formfields import richtext


class RichTextField(JSONField):
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', richtext.RichTextField)
        return super().formfield(**kwargs)
