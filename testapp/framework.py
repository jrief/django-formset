import itertools
import json

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.renderers import get_default_renderer
from django.db.models import Model, QuerySet
from django.db.models.fields.files import FieldFile
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import get_resolver, path, reverse
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView, UpdateView

from docutils.frontend import OptionParser
from docutils.io import StringOutput
from docutils.utils import new_document
from docutils.parsers.rst import Parser
from docutils.writers import get_writer_class

from formset.utils import FormMixin
from formset.views import FileUploadMixin, IncompleteSelectResponseMixin, FormCollectionView, FormViewMixin

from testapp.forms.address import AddressForm
from testapp.forms.complete import CompleteForm
from testapp.forms.contact import SimpleContactCollection, ContactCollection, ContactCollectionList
from testapp.forms.customer import CustomerCollection
from testapp.forms.opinion import OpinionForm
from testapp.forms.person import ButtonActionsForm, SimplePersonForm, sample_person_data, ModelPersonForm
from testapp.forms.questionnaire import QuestionnaireForm
from testapp.forms.richtext import RichTextForm
from testapp.forms.upload import UploadForm
from testapp.models import PersonModel


parser = Parser()


class JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, (UploadedFile, FieldFile)):
            return o.name
        if isinstance(o, Model):
            return str(o)
        if isinstance(o, QuerySet):
            return [str(i) for i in o]
        return super().default(o)


def render_suburls(request, extra_context=None):
    all_urls = set(filter(lambda url: url, (v[0][0][0] for v in get_resolver(__name__).reverse_dict.values())))
    all_urls.remove('success')
    context = {
        'framework': request.resolver_match.app_name,
        'all_urls': sorted(all_urls),
    }
    if extra_context:
        context.update(extra_context)
    template = get_template('index.html')
    return HttpResponse(template.render(context))


class SuccessView(TemplateView):
    template_name = 'success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'framework': self.request.resolver_match.app_name,
            'leaf_breadcrumb': "Success",
            'valid_formset_data': self.request.session.get('valid_formset_data'),
        })
        return context


class DemoViewMixin(IncompleteSelectResponseMixin, FileUploadMixin, FormViewMixin):
    def get_success_url(self):
        return reverse(f'{self.request.resolver_match.app_name}:form_data_valid')

    @property
    def framework(self):
        return self.request.resolver_match.app_name

    @property
    def mode(self):
        if self.request.resolver_match.url_name:
            return self.request.resolver_match.url_name.split('.')[-1]

    def get_css_classes(self):
        css_classes = dict(demo_css_classes[self.framework].get('*', {}))
        css_classes.update(demo_css_classes[self.framework].get(self.mode, {}))
        return css_classes

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.framework != 'default':
            context_data.update(framework=self.framework)
        holder_class = self.collection_class if isinstance(self, FormCollectionView) else self.form_class
        context_data.update(
            leaf_name=holder_class.__name__,
            **self.get_css_classes(),
        )
        if holder_class.__doc__:
            template = settings.BASE_DIR / 'testapp/templates/docutils.txt'
            writer = get_writer_class('html5')()
            docsettings = OptionParser(components=(Parser, writer), defaults={'template': template}).get_default_values()
            document = new_document('rst-doc', settings=docsettings)
            unindent = min(len(l) - len(l.lstrip()) for l in holder_class.__doc__.splitlines() if l)
            docstring = [l[unindent:] for l in holder_class.__doc__.splitlines()]
            if self.extra_doc:
                docstring.append('\n')
                docstring.extend(self.extra_doc.splitlines())
            docstring.extend(['', '------'])
            parser.parse('\n'.join(docstring), document)
            destination = StringOutput(encoding='utf-8')
            writer.write(document, destination)
            context_data['doc'] = mark_safe(destination.destination.decode('utf-8'))

        return context_data

    def extract_docstring(self):
        pass


class DemoFormViewMixin(DemoViewMixin):
    template_name = 'testapp/native-form.html'
    extra_doc = None

    def form_valid(self, form):
        self.request.session['valid_formset_data'] = json.dumps(
            form.cleaned_data, cls=JSONEncoder, indent=2, ensure_ascii=False
        )
        return super().form_valid(form)

    def get_form_class(self):
        form_class = super().get_form_class()
        assert not issubclass(form_class, FormMixin)
        attrs = self.get_css_classes()
        attrs.pop('button_css_classes', None)
        renderer_class = import_string(f'formset.renderers.{self.framework}.FormRenderer')
        if self.mode != 'native':
            renderer = renderer_class(**attrs)
            form_class = type(form_class.__name__, (FormMixin, form_class), {'default_renderer': renderer})
        return form_class


class DemoFormView(DemoFormViewMixin, FormView):
    pass


class DemoModelFormView(DemoFormViewMixin, UpdateView):
    model = PersonModel
    form_class = ModelPersonForm

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.session.session_key)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.last()

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.session.session_key:
            self.request.session.cycle_key()
        form.instance.created_by = self.request.session.session_key
        form.instance.save(update_fields=['created_by'])
        return response


class DemoFormCollectionView(DemoViewMixin, FormCollectionView):
    template_name = 'testapp/form-collection.html'
    extra_doc = None

    def get_collection_class(self):
        collection_class = super().get_collection_class()
        attrs = self.get_css_classes()
        attrs.pop('button_css_classes', None)
        renderer_class = import_string(f'formset.renderers.{self.framework}.FormRenderer')
        collection_class.default_renderer = renderer_class(**attrs)
        return collection_class

    def get_form_collection(self):
        """
        This method replaces the form renderer by a specialized version is specified in css_classes.
        Used to show how to style forms nested inside collections.
        """
        def traverse_holders(declared_holders, path=None):
            for name, holder in declared_holders.items():
                key = f'{path}.{name}' if path else name
                if hasattr(holder, 'declared_holders'):
                    traverse_holders(holder.declared_holders, key)
                elif key in css_classes:
                    holder.renderer = form_collection.default_renderer.__class__(**css_classes[key])
                else:
                    holder.renderer = get_default_renderer()

        css_classes = demo_css_classes[self.framework]
        form_collection = super().get_form_collection()
        traverse_holders(form_collection.declared_holders)
        return form_collection

    def form_collection_valid(self, form_collection):
        self.request.session['valid_formset_data'] = json.dumps(
            form_collection.cleaned_data, cls=JSONEncoder, indent=2, ensure_ascii=False
        )
        return super().form_collection_valid(form_collection)


demo_css_classes = {
    'default': {'*': {}},
    'bootstrap': {
        '*': {
            'field_css_classes': 'mb-2',
            'fieldset_css_classes': 'border p-3',
            'button_css_classes': 'mt-2',
        },
        'address': {
            'form_css_classes': 'row',
            'field_css_classes': {
                '*': 'mb-2 col-12',
                'postal_code': 'mb-2 col-4',
                'city': 'mb-2 col-8',
            },
        },
        'horizontal': {
            'field_css_classes': 'row mb-3',
            'label_css_classes': 'col-sm-3',
            'control_css_classes': 'col-sm-9',
            'button_css_classes': 'offset-sm-3',
        },
        'simplecontact': {
            'form_css_classes': 'row',
            'field_css_classes': {
                '*': 'col-12 mb-2',
                'profession.company': 'col-6 mb-2',
                'profession.job_title': 'col-6 mb-2',
            },
        },
        'numbers.number': {
            'form_css_classes': 'row',
            'field_css_classes': {
                'phone_number': 'mb-2 col-8',
                'label': 'mb-2 col-4',
                '*': 'mb-2 col-12',
            },
        }
    },
    'bulma': {
        '*': {
            'field_css_classes': 'mb-2',
        },
    },
    'foundation': {},
    'tailwind': {
        '*': {'field_css_classes': 'mb-4'},
        'address': {
            'form_css_classes': 'flex flex-wrap -mx-3',
            'field_css_classes': {
                '*': 'mb-4 px-3 w-full',
                'postal_code': 'mb-4 px-3 w-2/5',
                'city': 'mb-4 px-3 w-3/5',
            },
        },
        'numbers.number': {
            'form_css_classes': 'flex flex-wrap -mx-3',
            'field_css_classes': {
                '*': 'mb-4 px-3 w-full',
                'phone_number': 'mb-4 px-3 w-3/4',
                'label': 'mb-4 px-3 w-1/4',
            },
        }
    },
    'uikit': {
        '*': {'field_css_classes': 'uk-margin-bottom'},
    },
}

extra_doc_native = """
Here we use a native Django Form instance to render the form suitable for the ``<django-formset>``-widget.

Then that form instance is rendered using the special template tag ``render_form``. The template used to
render such a form shall be written as:

.. code-block:: django

	{% load render_form from formsetify %}

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form field_classes=... form_classes=... fieldset_classes=... label_classes=... control_classes=... %}
	</django-formset>
"""


extra_doc_extended = """
Here we use a Django Form instance with a overridden render method suitable for the ``<django-formset>``-widget.

This allows us to use the built-in ``__str__()``-method and hence render the form using ``{{ form }}`` inside a
template. In this use case, our Form class must additionally inherit from ``formset.utils.FormMixin``.

Such a Form class can for instance be defined as:

.. code-block:: python

	from django.forms import forms, fields
	from formset.utils import FormMixin

	class CompleteForm(FormMixin, forms.Form):
	    last_name = …

An instantiated Form object then can be rendered by a template using Django's variable expansion instead of a special
templatetag:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form }}
	  ...
	</django-formset>
"""


extra_doc_field_by_field = """
By rendering field-by-field, we get an even more fine grained control over how each field is rendered.

This way we can render each field in a different manner depending on its name or type. Such a template
might look like:

.. code-block:: django

	{% load formsetify %}
	...
	{% formsetify form %}
	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  <form>
	    {% include "formset/non_field_errors.html" %}
	    {% for field in form %}
	      {% if field.is_hidden %}
	        {{ field }}
	      {% elif field.name == "my_special_field" %}
	        {% include "myproject/my_special_field.html" %}
	      {% else %}
	        {% include "formset/default/field_group.html" %}
	      {% endif %}
	    {% endfor %}
	  </form>
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>
"""


extra_doc_horizontal = """
Here we render a Django Form instance using the template tag with different CSS classes:

.. code-block:: django

	{% render_form form "bootstrap" field_css_classes="row mb-3" label_css_classes="col-sm-3" control_css_classes="col-sm-9" %}

When using the Bootstrap framework, they align the label and the field on the same row rather
than placing them below each other.
"""


urlpatterns = [
    path('', render_suburls),
    path('success', SuccessView.as_view(), name='form_data_valid'),
    path('01-complete.native', DemoFormView.as_view(
        form_class=CompleteForm,
        extra_doc=extra_doc_native,
    ), name='complete.native'),
    path('02-complete.extended', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/extended-form.html',
        extra_doc=extra_doc_extended,
    ), name='complete.extended'),
    path('03-complete.field-by-field', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/field-by-field.html',
        extra_doc=extra_doc_field_by_field,
    ), name='complete.field-by-field'),
    path('04-complete.horizontal', DemoFormView.as_view(
        form_class=CompleteForm,
        extra_doc=extra_doc_horizontal,
    ), name='complete.horizontal'),
    path('05-address', DemoFormView.as_view(
        form_class=AddressForm,
    ), name='address'),
    path('06-opinion', DemoFormView.as_view(
        form_class=OpinionForm,
    ), name='opinion'),
    path('07-questionnaire', DemoFormView.as_view(
        form_class=QuestionnaireForm,
    ), name='questionnaire'),
    path('08-simplecontact', DemoFormCollectionView.as_view(
        collection_class=SimpleContactCollection,
        initial={'person': sample_person_data},
    ), name='simplecontact'),
    path('09-customer', DemoFormCollectionView.as_view(
        collection_class=CustomerCollection,
    ), name='customer'),
    path('10-contact', DemoFormCollectionView.as_view(
        collection_class=ContactCollection,
        initial={'person': sample_person_data, 'numbers': [{'number': {'phone_number': "+1 234 567 8900"}}]},
    ), name='contact'),
    path('11-contactlist', DemoFormCollectionView.as_view(
        collection_class=ContactCollectionList,
    ), name='contactlist'),
    path('12-upload', DemoFormView.as_view(
        form_class=UploadForm,
    ), name='upload'),
    path('13-richtext', DemoFormView.as_view(
        form_class=RichTextForm,
    ), name='upload'),
    path('14-person', DemoModelFormView.as_view(
        form_class=ModelPersonForm,
        model=PersonModel,
    ), name='person'),
    path('15-button-actions', DemoFormView.as_view(
        form_class=ButtonActionsForm,
        template_name='testapp/button-actions.html',
        extra_context={'click_actions': 'clearErrors -> disable -> spinner -> submit -> okay(1500) -> proceed !~ enable -> bummer(9999)'},
    ), name='button-actions'),
]

# this creates permutations of forms to show how to withhold which feedback
withhold_feedbacks = ['messages', 'errors', 'warnings', 'success']
extra_doc_withhold = {
    'messages': "that error messages below the field will not be rendered when the user blurs a field with "
                "invalid data.",
    'errors': "that the border does not change color (usually red) and the field does not show an alert symbol, "
              "when the user blurs a field with invalid data.",
    'warnings': "that the field does not show a warning symbol (usually orange), when a field has focus, "
                "but its content does not contain valid data (yet). If only ``errors`` has been added to "
                "``withhold-feedback=\"...\"``, then the warning symbol will remain even if the field looses focus.",
    'success': "that the border does not change color (usually green) and the field does not show a success symbol,"
               "when the user blurs a field with valid data.",
}
for length in range(len(withhold_feedbacks) + 1):
    for withhold_feedback in itertools.combinations(withhold_feedbacks, length):
        suffix = '.' + ''.join(w[0] for w in withhold_feedback) if length else ''
        if withhold_feedback:
            extra_docs = ['------', '', 'Using ``withhold-feedback="{}"`` means:'.format(' '.join(withhold_feedback)), '']
        else:
            extra_docs = []
        extra_docs.extend([f'* {extra_doc_withhold[w]}' for w in withhold_feedback])
        force_submission = suffix == '.mews'  # just for testing
        urlpatterns.append(
            path(f'16-withhold{suffix}', DemoFormView.as_view(
                form_class=SimplePersonForm,
                extra_context={
                    'withhold_feedback': ' '.join(withhold_feedback),
                    'force_submission': force_submission,
                },
                extra_doc='\n'.join(extra_docs),
            ))
        )
