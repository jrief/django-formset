import json
import types

from django.contrib import admin as django_admin
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.exceptions import PermissionDenied
from django.db.models.fields import BooleanField
from django.db.models.fields.files import FileField
from django.http import HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext

from formset.forms import ModelFormMixin, FormsetModelFormMetaclass
from formset.renderers.admin import FormRenderer
from formset.upload import receive_uploaded_file
from formset.calendar import CalendarResponseMixin
from formset.views import IncompleteSelectResponseMixin
from formset.widgets import UploadedFileInput


class ModelAdminMixin(CalendarResponseMixin, IncompleteSelectResponseMixin):
    change_form_template = 'admin/formset/change_form.html'
    formfield_overrides = {
        BooleanField: {'label_suffix': ''},
        FileField: {'widget': UploadedFileInput},
    }

    def get_form(self, request, obj=None, change=False, **kwargs):
        def init(self, *args, **kwargs):
            # change signature of constructor to keep compatible with Django's ModelAdmin forms
            super(self.__class__, self).__init__(*args, **kwargs)

        form = super().get_form(request, obj, change, **kwargs)
        field_css_classes = {key: f'field-{key}' for key in form.base_fields.keys()}
        # we have to add fields using our own widgets (`Selectize`, `SelectizeMultiple` and `DualSelector`) to
        # `raw_id_fields` in order to prevent Django from rendering them inside a `RelatedFieldWidgetWrapper`.
        # See ticket https://code.djangoproject.com/ticket/36250 for details.
        self.raw_id_fields = [
            name for name, field in form.base_fields.items()
            if isinstance(field.widget, RelatedFieldWidgetWrapper)
        ] + list(self.raw_id_fields)
        if issubclass(form, ModelFormMixin):
            form.default_renderer = FormRenderer(field_css_classes=field_css_classes)
        else:
            form = types.new_class(
                form.__name__,
                bases=(ModelFormMixin, form),
                kwds={'metaclass': FormsetModelFormMetaclass},
                exec_body=lambda ns: ns.update({
                    '__init__': init,
                    'default_renderer': FormRenderer(field_css_classes=field_css_classes),
                }),
            )
        return form

    def get_field(self, field_path):
        field_name = field_path.split('.')[-1]
        return self.form_class.base_fields[field_name]

    def _changeform_view(self, request, object_id, form_url, extra_context):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise django_admin.DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if request.method == "POST":
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
            else:
                if not self.has_view_or_change_permission(request, obj):
                    raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(
                    request, self.opts, object_id
                )

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(
            request, obj, change=not add, fields=flatten_fieldsets(fieldsets)
        )
        if request.method == "POST":
            if request.content_type == 'application/json':
                request_body = json.loads(request.body)
                formset_data = request_body.get('formset_data')
                request_target = request_body.get('_extra', {}).get('name')
            elif request.content_type == 'multipart/form-data' and 'temp_file' in request.FILES and 'image_height' in request.POST:
                try:
                    return JsonResponse(
                        receive_uploaded_file(request.FILES['temp_file'], request.POST['image_height'])
                    )
                except Exception as e:
                    return HttpResponseBadRequest(str(e))

            if request_target == '_saveasnew':
                form = ModelForm(data=formset_data)
            else:
                form = ModelForm(data=formset_data, instance=obj)
            # formsets, inline_instances = self._create_formsets(
            #     request,
            #     form.instance,
            #     change=not add,
            # )
            if form.is_valid():
                new_object = form.save()
                if request_target == '_save' or request_target == '_saveasnew' and not self.save_as_continue:
                    success_url = reverse(
                        f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist',
                        current_app=self.admin_site.name,
                    )
                elif request_target == '_addanother':
                    success_url = reverse(
                        f'admin:{self.opts.app_label}_{self.opts.model_name}_add',
                        current_app=self.admin_site.name,
                    )
                else:
                    assert request_target == '_continue' or request_target == '_saveasnew' and self.save_as_continue
                    success_url = reverse(
                        f'admin:{self.opts.app_label}_{self.opts.model_name}_change',
                        args=(new_object.pk,),
                        current_app=self.admin_site.name,
                    )
                return JsonResponse({'success_url': success_url})
            else:
                return JsonResponse(form.errors, status=422, safe=False)
        else:
            if 'calendar' in request.GET or 'field' in request.GET:
                self.form_class = ModelForm
                return self.get(request)

            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(
                    request, form.instance, change=False
                )
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(
                    request, obj, change=True
                )

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(fieldsets)
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        admin_form = helpers.AdminForm(
            form,
            list(fieldsets),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            (
                self.get_prepopulated_fields(request, obj)
                if add or self.has_change_permission(request, obj)
                else {}
            ),
            readonly_fields,
            model_admin=self,
        )
        media = self.media + admin_form.media

        inline_formsets = self.get_inline_formsets(
            request, formsets, inline_instances, obj
        )
        for inline_formset in inline_formsets:
            media += inline_formset.media

        if add:
            title = gettext("Add %s")
        elif self.has_change_permission(request, obj):
            title = gettext("Change %s")
        else:
            title = gettext("View %s")
        context = {
            **self.admin_site.each_context(request),
            "title": title % self.opts.verbose_name,
            "subtitle": str(obj) if obj else None,
            "adminform": admin_form,
            "object_id": object_id,
            "original": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": django_admin.helpers.AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
        }
        context.update(extra_context or {})

        return self.render_change_form(
            request, context, add=add, change=not add, obj=obj, form_url=form_url
        )


class ModelAdmin(ModelAdminMixin, django_admin.ModelAdmin):
    """
    Base class for all Django ModelAdmin classes using django-formset forms instead of the default.
    """
