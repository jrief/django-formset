import json
import types
import warnings

from django.contrib import admin as django_admin
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR, get_content_type_for_model
from django.db import transaction
from django.db.models.fields import BooleanField
from django.db.models.fields.files import FileField
from django.http import HttpResponseBadRequest, JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext

from formset.calendar import CalendarResponseMixin
from formset.forms import FormsetModelFormMetaclass, ModelFormMixin
from formset.renderers.admin import FormRenderer
from formset.upload import receive_uploaded_file
from formset.views import FormCollectionViewMixin, IncompleteSelectResponseMixin
from formset.widgets import UploadedFileInput


class ModelAdminMixin(CalendarResponseMixin, IncompleteSelectResponseMixin, FormCollectionViewMixin):
    change_form_template = 'admin/formset/change_form.html'
    formfield_overrides = {
        BooleanField: {'label_suffix': ''},
        FileField: {'widget': UploadedFileInput},
    }
    form_renderer_class = FormRenderer

    def __init__(self, *args, **kwargs):
        if self.fields is not None:
            warnings.warn(
                f"Adding `field` to {self.__class__.__name__} has no effect. "
                "Use `form` referring to a class inheriting from `formset.forms.ModelForm` instead.",
                RuntimeWarning,
                stacklevel=2,
            )
        if self.fieldsets is not None:
            warnings.warn(
                f"Adding `fieldsets` to {self.__class__.__name__} has no effect. "
                "Use `formset.fieldset.Fieldset` instead.",
                RuntimeWarning,
            )
        if len(self.inlines) > 0:
            warnings.warn(
                f"Adding `inlines` to {self.__class__.__name__} has no effect. "
                "Use a class inheriting from `formset.collection.FormCollection` instead of a form.",
                RuntimeWarning,
            )
        if len(self.raw_id_fields) > 0:
            warnings.warn(
                f"Adding `raw_id_fields` to {self.__class__.__name__} has no effect. "
                "Use `formset.widgets.Selectize` in your form class instead.",
                RuntimeWarning,
            )
        if len(self.readonly_fields) > 0:
            warnings.warn(
                f"Adding `readonly_fields` to {self.__class__.__name__} has no effect. "
                "Use disabled fields in your form instead.",
                RuntimeWarning,
            )
        super().__init__(*args, **kwargs)

    def get_model_form(self):
        def init(self, *args, **kwargs):
            # change signature of constructor to keep compatible with Django's ModelAdmin forms
            super(self.__class__, self).__init__(*args, **kwargs)

        field_css_classes = {key: f'field-{key}' for key in self.form.base_fields.keys()}
        default_renderer = self.form_renderer_class(field_css_classes=field_css_classes)
        if issubclass(self.form, ModelFormMixin):
            return type(self.form.__name__, (self.form,), {'default_renderer': default_renderer})
        else:
            return types.new_class(
                self.form.__name__,
                bases=(ModelFormMixin, self.form),
                kwds={'metaclass': FormsetModelFormMetaclass},
                exec_body=lambda ns: ns.update({
                    '__init__': init,
                    'default_renderer': default_renderer,
                }),
            )

    def get_field(self, field_path):
        if self.collection_class:
            return self.collection_class().get_field(field_path)
        field_name = field_path.split('.')[-1]
        return self.form().base_fields[field_name]

    def get_collection_kwargs(self):
        kwargs = super().get_collection_kwargs()
        kwargs.update({
            'renderer': self.form_renderer_class(),
        })
        return kwargs

    def _changeform_view(self, request, object_id, form_url, extra_context):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise django_admin.DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        if request.method == 'GET' and ('calendar' in request.GET or 'field' in request.GET):
            # intercept calendar requests
            return super().get(request)

        if request.method == 'POST' and request.content_type == 'multipart/form-data' and 'temp_file' in request.FILES:
            # intercept file uploads
            try:
                return JsonResponse(
                    receive_uploaded_file(request.FILES['temp_file'], request.POST['image_height'])
                )
            except Exception as e:
                return HttpResponseBadRequest(str(e))

        if object_id:
            add = False
            self.object = self.get_object(request, object_id)
        else:
            add = True
            self.object = self.model()
        self.request = request
        kwargs = {}
        if collection_class := self.get_collection_class():
            initial = collection_class().model_to_dict(self.object)
            kwargs.update(self.get_collection_kwargs())
        else:
            initial = self.get_changeform_initial_data(request)
        kwargs.update(initial=initial, instance=self.object)

        if self.request.method in ('PATCH', 'POST', 'PUT') and self.request.content_type == 'application/json':
            return self._update_collection_view(kwargs)

        # render the form or collection to HTML
        if add:
            title = gettext("Add {title}")
        elif self.has_change_permission(request, self.object):
            title = gettext("Change {title}")
        else:
            title = gettext("View {title}")

        if collection_class := self.get_collection_class():
            form_or_collection = collection_class(**kwargs)
        else:
            form_or_collection = self.get_model_form()(**kwargs)
        admin_form = helpers.AdminForm(
            form_or_collection,
            [],
            {},
            [],
            model_admin=self,
        )
        media = self.media + admin_form.media

        context = {
            **self.admin_site.each_context(request),
            "title": title.format(title=self.opts.verbose_name),
            "subtitle": str(self.object) if self.object.pk and hasattr(self.object, '__str__') else None,
            "form": form_or_collection,
            "object_id": self.object.pk if self.object else None,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "media": media,
            "preserved_filters": self.get_preserved_filters(request),
        }
        context.update(extra_context or {})
        return self.render_change_form(
            request, context, add=add, change=not add, obj=self.object, form_url=form_url
        )

    def _update_collection_view(self, view_kwargs):
        if self.get_extra_data().get('name') == '_saveasnew':
            self.object = self.model()
        body = json.loads(self.request.body)
        view_kwargs.update(data=body.get('formset_data'))
        if collection_class := self.get_collection_class():
            form_collection = collection_class(**view_kwargs)
            if form_collection.is_valid():
                with transaction.atomic():
                    form_collection.construct_instance(self.object)
                # integrity errors may occur during construction, hence revalidate collection
                if form_collection.is_valid():
                    return self.render_success_response()
                else:
                    return JsonResponse(form_collection._errors, status=422, safe=False)
            else:
                return JsonResponse(form_collection._errors, status=422, safe=False)
        else:
            model_form = self.get_model_form()(**view_kwargs)
            if model_form.is_valid():
                self.object = model_form.save()
                return self.render_success_response()
            else:
                return JsonResponse(model_form.errors, status=422, safe=False)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        app_label = self.opts.app_label
        view_on_site_url = self.get_view_on_site_url(obj)
        context.update({
            "add": add,
            "change": change,
            "has_view_permission": self.has_view_permission(request, obj),
            "has_add_permission": self.has_add_permission(request),
            "has_change_permission": self.has_change_permission(request, obj),
            "has_delete_permission": self.has_delete_permission(request, obj),
            "has_editable_inline_admin_formsets": False,
            "has_absolute_url": view_on_site_url is not None,
            "absolute_url": view_on_site_url,
            "opts": self.opts,
            "content_type_id": get_content_type_for_model(self.model).pk,
            "save_as": self.save_as,
            "save_on_top": self.save_on_top,
            "to_field_var": TO_FIELD_VAR,
            "is_popup_var": IS_POPUP_VAR,
            "app_label": app_label,
        })
        if add and self.add_form_template is not None:
            form_template = self.add_form_template
        else:
            form_template = self.change_form_template

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            form_template
            or [
                "admin/{0}/{1}/change_form.html".format(app_label, self.opts.model_name),
                "admin/{0}/change_form.html".format(app_label),
                "admin/formset/change_form.html",
            ],
            context,
        )

    def render_success_response(self):
        name = self.get_extra_data().get('name')
        if name == '_save' or name == '_saveasnew' and self.save_as_continue:
            success_url = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist')
        elif name == '_addanother':
            success_url = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_add')
        else:
            success_url = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_change', args=(self.object.pk,))
        return JsonResponse({'success_url': success_url})


class ModelAdmin(ModelAdminMixin, django_admin.ModelAdmin):
    """
    Base class for all Django ModelAdmin classes using django-formset forms instead of the default.
    """
