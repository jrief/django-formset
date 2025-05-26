import json

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import QuerySet
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse

try:
    from django.utils.choices import CallableChoiceIterator
except ImportError:  # Django<5.0
    from django.forms.fields import CallableChoiceIterator

from django.utils.encoding import force_str
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView as GenericFormView

from formset.upload import FileUploadMixin
from formset.utils import CollectionFieldMixin
from formset.widgets.models import IncompleteSelectMixin


class IncompleteSelectResponseMixin:
    """
    Add this mixin to any Django View class using forms with incomplete fields. These fields
    usually are of type ChoiceField referring to a foreign model and using one of the widgets
    :class:`formset.widgets.Selectize`, :class:`formset.widgets.SelectizeMultiple` or
    :class:`formset.widgets.DualSelector`.
    """
    def get(self, request, **kwargs):
        if request.accepts('application/json') and 'field' in request.GET:
            return self._fetch_options(request)
        return super().get(request, **kwargs)

    def _fetch_options(self, request):
        field_path = request.GET['field']
        try:
            field = self.get_field(field_path)
        except (KeyError, ValueError):
            return HttpResponseBadRequest(f"No such field: {field_path}")
        assert isinstance(field.widget, IncompleteSelectMixin), (
            f"Field {field_path} must use a widget inheriting from `IncompleteSelectMixin`."
        )
        widget = field.widget
        try:
            offset = int(request.GET.get('offset'))
        except TypeError:
            offset = 0

        if isinstance(widget.choices, CallableChoiceIterator):
            options = [
                o for index, o in enumerate(widget.choices)
                if index >= offset and index < offset + widget.max_prefetch_choices
            ]
            return JsonResponse({
                'count': len(options),
                'incomplete': False,
                'options': options,
            })

        queryset = widget.choices.queryset
        data = {'total_count': queryset.count()}
        incomplete = queryset.count() - offset > widget.max_prefetch_choices

        if widget.filter_by and any(k.startswith('filter-') for k in request.GET.keys()):
            filtervalues = {key: request.GET.getlist(f'filter-{key}') for key in widget.filter_by.keys()}
            queryset = queryset.filter(widget.build_filter_query(filtervalues))
            incomplete = None  # incomplete state unknown
        elif widget.use_filter_set:
            queryset = widget.use_filter_set(request=request, queryset=queryset).qs
            incomplete = None  # incomplete state unknown

        if pk := request.GET.get('pk'):
            queryset = queryset.filter(pk=pk)
            incomplete = None  # incomplete state unknown
        elif search := request.GET.get('search'):
            data['search'] = search
            queryset = queryset.filter(widget.build_search_query(search))
            incomplete = None  # incomplete state unknown

        limited_qs = queryset[offset:offset + widget.max_prefetch_choices]
        to_field_name = field.to_field_name if field.to_field_name else 'pk'
        if widget.group_field_name:
            options = [{
                'id': getattr(item, to_field_name),
                'label': str(item),
                'optgroup': force_str(getattr(item, widget.group_field_name)),
            } for item in limited_qs]
        else:
            options = [{
                'id': getattr(item, to_field_name),
                'label': str(item),
            } for item in limited_qs]
        data.update(
            count=len(options),
            incomplete=incomplete,
            options=options,
        )
        return JsonResponse(data)


class FormsetResponseMixin:
    @property
    def _request_body(self):
        if self.request.content_type == 'application/json':
            if not isinstance(getattr(self.request, '_parsed_body', None), dict):
                self.request._parsed_body = json.loads(self.request.body)
            return self.request._parsed_body

    def get_extra_data(self):
        """
        When submitting a form, one can additionally add extra parameters via the button's ``submit()`` action.
        Use this method to access that extra data.
        """
        if self._request_body:
            return self._request_body.get('_extra')


class FormViewMixin(FormsetResponseMixin):
    """
    Add this mixin to a view class inheriting from one of the Django form view classes. It serves to respond
    with a JsonResponse rather than a HttpResponse whenever a form submission validates or fails.
    """

    form_kwargs = None

    def get_success_url(self):
        """
        In **django-formset**, the success_url may be None and set inside the templates.
        """
        return str(self.success_url) if self.success_url else None

    def form_valid(self, form):
        response = super().form_valid(form)
        assert response.status_code == 302
        return JsonResponse({'success_url': self.get_success_url()})

    def form_invalid(self, form):
        super().form_invalid(form)
        return JsonResponse(form.errors, status=422, safe=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.form_kwargs:
            kwargs.update(**self.form_kwargs)
        if self._request_body:
            kwargs['data'] = self._request_body.get('formset_data')
        return kwargs

    def get_field(self, field_path):
        parts = field_path.split('.')
        if parts[0] == '__default__':
            return self.form_class.base_fields[parts[1]]
        if isinstance(self.form_class.base_fields[parts[0]], CollectionFieldMixin):
            return self.form_class.base_fields[parts[0]].collection.get_field('.'.join(parts[1:]))
        raise KeyError(f"Field {field_path} not found in formset {self.form_class.__name__}.")


class FormView(IncompleteSelectResponseMixin, FileUploadMixin, FormViewMixin, GenericFormView):
    """
    FormView class used as controller for handling a single Django Form. The purpose of this View
    is to render the provided Form, when invoked as a standard GET-request using the provided Django
    Template.
    This View also acts as endpoint for POST-requests submitting files, as endpoint for GET-requests
    querying for autocomplete Select-Fields and as endpoint for Form submissions.

    It can be used directly inside the URL routing:

    .. code-block:: python

        from django.urls import path
        from formset.views import FormView

        ...
        urlpatterns = [
            ...
            path('my-uri', FormView.as_view(
                form_class=MyForm,
                template_name='my-form.html',
                success_url='/success',
            )),
            ...
        ]

    or by inheriting from ``FormView`` and overwriting the attributes in that class:

    .. code-block:: python

        from formset.views import FormView

        class MyFormEditView(FormView):
            form_class = MyForm
            template_name = 'my-form.html'
            success_url = '/success'
    """


class FormCollectionViewMixin(FormsetResponseMixin):
    collection_class = None
    success_url = None
    initial = {}
    collection_kwargs = None

    def get(self, request, *args, **kwargs):
        if request.accepts('application/json') and set(['path', 'pk']).issubset(request.GET):
            # invoked by `DjangoFormset.prefillPartial()`
            return self._fetch_partial_data()
        # instantiate blank versions of the forms in the collection
        return self.render_to_response(self.get_context_data())

    def post(self, request, **kwargs):
        form_collection = self.get_form_collection()
        if form_collection.is_valid():
            return self.form_collection_valid(form_collection)
        else:
            return self.form_collection_invalid(form_collection)

    def patch(self, request, **kwargs):
        """
        Method `PATCH` is used for partial submits.
        """
        return self.post(request, **kwargs)

    def delete(self, request, **kwargs):
        """
        Method `DELETE` is used for partial deletion.
        """
        if set(['path', 'pk']).issubset(request.GET):
            return self._delete_partial()
        return HttpResponseForbidden("Method DELETE not supported in this context")

    def _fetch_partial_data(self):
        collection_class = self.get_collection_class()
        empty_holder = collection_class
        initial = self.get_initial()
        bucket = None
        for part in self.request.GET['path'].split('.'):
            if not (empty_holder := empty_holder.declared_holders.get(part)):
                break
            bucket = initial.setdefault(part, {})
        if bucket is not None:
            try:
                instance = empty_holder._meta.model.objects.get(pk=self.request.GET.get('pk'))
                bucket.update(**type(empty_holder)(instance=instance).initial)
            except empty_holder._meta.model.DoesNotExist:
                pass
            else:
                return JsonResponse(initial)
        return HttpResponseBadRequest("Invalid path value")

    def _delete_partial(self):
        collection_class = self.get_collection_class()
        empty_holder = collection_class
        for part in self.request.GET['path'].split('.'):
            if not (empty_holder := empty_holder.declared_holders.get(part)):
                break
        if empty_holder is not None:
            try:
                instance = empty_holder._meta.model.objects.get(pk=self.request.GET.get('pk'))
            except empty_holder._meta.model.DoesNotExist:
                pass
            else:
                instance.delete()
                return HttpResponse(status=204)
        return HttpResponseBadRequest("Invalid path value")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_collection'] = self.get_form_collection()
        return context

    def get_field(self, field_path):
        collection_class = self.get_collection_class()
        return collection_class().get_field(field_path)

    def get_collection_kwargs(self):
        kwargs = {
            'initial': self.get_initial(),
            'partial': self.request.method == 'PATCH',
        }
        if self.collection_kwargs:
            kwargs.update(**self.collection_kwargs)
        return kwargs

    def get_form_collection(self):
        collection_class = self.get_collection_class()
        kwargs = self.get_collection_kwargs()
        if self.request.method in ('PATCH', 'POST', 'PUT') and self.request.content_type == 'application/json':
            body = json.loads(self.request.body)
            kwargs.update(data=body.get('formset_data'))
            if callable(getattr(self, 'get_object', None)):
                kwargs.update(instance=self.get_object())
        return collection_class(**kwargs)

    def get_collection_class(self):
        return self.collection_class

    def get_initial(self):
        """Return the initial data to use for collections of forms on this view."""
        return self.initial.copy()

    def get_success_url(self):
        return str(self.success_url) if self.success_url else None

    def form_collection_valid(self, form_collection):
        return JsonResponse({'success_url': self.get_success_url()})

    def form_collection_invalid(self, form_collection):
        return JsonResponse(form_collection._errors, status=422, safe=False)


class FormCollectionView(IncompleteSelectResponseMixin, FileUploadMixin, FormCollectionViewMixin, ContextMixin,
                         TemplateResponseMixin, View):
    pass


class EditCollectionView(IncompleteSelectResponseMixin, FileUploadMixin, FormCollectionViewMixin, SingleObjectMixin,
                         TemplateResponseMixin, View):
    """
    View for editing a class inheriting from `FormCollection` which binds to a single object.
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if isinstance(initial, dict) and self.object:
            collection_class = self.get_collection_class()
            initial.update(collection_class().model_to_dict(self.object))
        return initial

    def form_collection_valid(self, form_collection):
        with transaction.atomic():
            form_collection.construct_instance(self.object)
        # integrity errors may occur during construction, hence revalidate collection
        if form_collection.is_valid():
            return super().form_collection_valid(form_collection)
        else:
            return self.form_collection_invalid(form_collection)


class BulkEditCollectionView(IncompleteSelectResponseMixin, FileUploadMixin, FormCollectionViewMixin, ContextMixin,
                             TemplateResponseMixin, View):
    """
    View for editing a class inheriting from `FormCollection` which binds to multiple objects.
    """
    queryset = None
    model = None
    ordering = None

    def get_ordering(self):
        return self.ordering

    def get_queryset(self):
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            class_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"{class_name} is missing a QuerySet. {class_name}.model, {class_name}.queryset, or override "
                f"{class_name}.get_queryset()."
            )
        if ordering := self.get_ordering():
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset

    def get_initial(self):
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class().models_to_list(queryset)
        return initial

    def form_collection_valid(self, form_collection):
        with transaction.atomic():
            form_collection.construct_instance()
        # integrity errors may occur during construction, hence revalidate collection
        if form_collection.is_valid():
            return super().form_collection_valid(form_collection)
        else:
            return self.form_collection_invalid(form_collection)
