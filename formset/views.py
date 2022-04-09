import json

from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.encoding import force_str
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from django.views.generic.edit import FormView as GenericFormView

from formset.upload import FileUploadMixin
from formset.widgets import Selectize, DualSelector


class IncompleSelectResponseMixin:
    def get(self, request, **kwargs):
        if request.accepts('application/json') and 'field' in request.GET:
            if 'query' in request.GET or 'offset' in request.GET:
                return self._fetch_options(request)
        return super().get(request, **kwargs)

    def _fetch_options(self, request):
        field_path = request.GET['field']
        try:
            field = self.get_field(field_path)
        except KeyError:
            return HttpResponseBadRequest(f"No such field: {field_path}")
        assert isinstance(field.widget, (Selectize, DualSelector))
        try:
            offset = int(request.GET.get('offset'))
        except TypeError:
            offset = 0
        if query := request.GET.get('query'):
            data = {'query': query}
            queryset = field.widget.search(query)
            incomplete = None  # incomplete state unknown
        else:
            data = {}
            queryset = field.widget.choices.queryset
            incomplete = queryset.count() - offset > field.widget.max_prefetch_choices
        limited_qs = queryset[offset:offset + field.widget.max_prefetch_choices]
        to_field_name = field.to_field_name if field.to_field_name else 'pk'
        items = [{'id': getattr(item, to_field_name), 'label': str(item)} for item in limited_qs]
        data.update(
            count=len(items),
            total_count=field.widget.choices.queryset.count(),
            incomplete=incomplete,
            items=items,
        )
        return JsonResponse(data)


class FormViewMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        assert response.status_code == 302
        response_data = {'success_url': force_str(response.url)} if response.url else {}
        return JsonResponse(response_data)

    def form_invalid(self, form):
        super().form_invalid(form)
        return JsonResponse(form.errors, status=422, safe=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.content_type == 'application/json':
            body = json.loads(self.request.body)
            kwargs['data'] = body.get('formset_data')
        return kwargs

    def get_field(self, path):
        field_name = path.split('.')[-1]
        return self.form_class.base_fields[field_name]


class FormView(IncompleSelectResponseMixin, FileUploadMixin, FormViewMixin, GenericFormView):
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

    """


class FormCollectionViewMixin(ContextMixin):
    collection_class = None
    success_url = None
    initial = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate blank versions of the forms in the collection."""
        return self.render_to_response(self.get_context_data())

    def post(self, request, **kwargs):
        form_collection = self.get_form_collection()
        if form_collection.is_valid():
            response_data = {'success_url': force_str(self.success_url)} if self.success_url else {}
            return JsonResponse(response_data)
        else:
            return JsonResponse(form_collection.errors, status=422, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_collection'] = self.get_form_collection()
        return context

    def get_field(self, path):
        return self.form_collection.get_field(path)

    def get_form_collection(self):
        collection_class = self.get_collection_class()
        kwargs = {
            'initial': self.get_initial(),
        }
        if self.request.method in ('POST', 'PUT') and self.request.content_type == 'application/json':
            body = json.loads(self.request.body)
            kwargs.update(data=body.get('formset_data'))
        return collection_class(**kwargs)

    def get_collection_class(self):
        return self.collection_class

    def get_initial(self):
        """Return the initial data to use for collections of forms on this view."""
        return self.initial.copy()


class FormCollectionView(IncompleSelectResponseMixin, FileUploadMixin, FormCollectionViewMixin, TemplateResponseMixin, View):
    pass
