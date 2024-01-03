import functools
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.forms.renderers import get_default_renderer
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import get_resolver, path
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView, UpdateView

from docutils.frontend import OptionParser
from docutils.io import StringOutput
from docutils.utils import new_document
from docutils.parsers.rst import Parser
from docutils.writers import get_writer_class

from formset.calendar import CalendarResponseMixin
from formset.utils import FormMixin
from formset.views import (
    FileUploadMixin, IncompleteSelectResponseMixin, FormCollectionView, FormCollectionViewMixin, FormViewMixin,
    EditCollectionView, BulkEditCollectionView
)

from testapp.demo_helpers import SessionFormCollectionViewMixin
from testapp.forms.address import AddressForm
from testapp.forms.advertisement import AdvertisementForm
from testapp.forms.article import ArticleForm
from testapp.forms.blog import BlogModelForm
from testapp.forms.complete import CompleteForm
from testapp.forms.contact import (
    SimpleContactCollection, ContactCollection, ContactCollectionList, IntermediateContactCollectionList,
    SortableContactCollection, SortableContactCollectionList)
from testapp.forms.birthdate import BirthdateBoxForm, BirthdateCalendarForm, BirthdateInputForm, BirthdatePickerForm
from testapp.forms.booking import BookingBoxForm, BookingCalendarForm, BookingPickerForm
from testapp.forms.country import CountryForm
from testapp.forms.county import CountyForm
from testapp.forms.customer import CustomerCollection
from testapp.forms.moment import MomentBoxForm, MomentCalendarForm, MomentInputForm, MomentPickerForm
from testapp.forms.moon import MoonForm, MoonCalendarRenderer
from testapp.forms.opinion import OpinionForm
from testapp.forms.person import ButtonActionsForm, sample_person_data, ModelPersonForm
from testapp.forms.phone import PhoneForm
from testapp.forms.poll import ModelPollForm, PollCollection
from testapp.forms.profile import ProfileCollection
from testapp.forms.questionnaire import QuestionnaireForm
from testapp.forms.schedule import ScheduleBoxForm, ScheduleCalendarForm, SchedulePickerForm
from testapp.forms.state import StateForm, StatesForm
from testapp.forms.company import CompanyCollection, CompaniesCollection
from testapp.forms.user import UserCollection, UserListCollection
from testapp.forms.upload import UploadForm
from testapp.forms.gallerycollection import GalleryCollection
from testapp.models import BlogModel, Company, PersonModel, PollModel
from testapp.models.gallery import Gallery


parser = Parser()


class JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, (UploadedFile, FieldFile)):
            return o.name
        if isinstance(o, Model):
            return repr(o)
        if hasattr(o, '__iter__'):
            return [self.default(i) for i in o]
        return super().default(o)


def render_suburls(request, extra_context=None):
    all_urls = filter(lambda url: url, (v[0][0][0] for v in get_resolver(__name__).reverse_dict.values()))
    all_urls = functools.reduce(lambda l, t: l.append(t) or l if t not in l else l, all_urls, [])
    context = {
        'framework': request.resolver_match.app_name,
        'all_urls': all_urls,
    }
    if extra_context:
        context.update(extra_context)
    template = get_template('testapp/index.html')
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


class DemoViewMixin:
    def get_success_url(self):
        return '/success'

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
        if isinstance(self, FormCollectionViewMixin):
            holder_class = self.collection_class
        else:
            holder_class = self.form_class
        context_data.update(
            leaf_name=holder_class.__name__,
            valid_formset_data=self.request.session.get('valid_formset_data'),
            **self.get_css_classes(),
        )
        self.request.session.pop('valid_formset_data', None)
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


class DemoFormViewMixin(DemoViewMixin, CalendarResponseMixin, IncompleteSelectResponseMixin, FileUploadMixin, FormViewMixin):
    template_name = 'testapp/native-form.html'
    extra_context = {
        'click_actions': 'disable -> submit -> reload !~ scrollToError'
    }
    extra_doc = None

    def form_valid(self, form):
        formset_data = json.loads(self.request.body)['formset_data']
        self.request.session['valid_formset_data'] = json.dumps(
            formset_data, cls=JSONEncoder, indent=2, ensure_ascii=False
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
        if form.instance.created_by != self.request.session.session_key:
            form.instance.created_by = self.request.session.session_key
            form.instance.save(update_fields=['created_by'])
        return response


class DemoFormCollectionViewMixin(DemoViewMixin):
    template_name = 'testapp/form-collection.html'
    extra_doc = None
    extra_context = {
        'click_actions': 'disable -> submit -> reload !~ scrollToError'
    }

    def get_collection_class(self):
        collection_class = super().get_collection_class()
        attrs = self.get_css_classes()
        attrs.pop('button_css_classes', None)
        renderer_class = import_string(f'formset.renderers.{self.framework}.FormRenderer')
        collection_class.default_renderer = renderer_class(**attrs)
        return collection_class

    def get_form_collection(self):
        """
        This method replaces the form renderer by a specialized version which is specified in css_classes.
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
        formset_data = json.loads(self.request.body)['formset_data']
        self.request.session['valid_formset_data'] = json.dumps(
            formset_data, cls=JSONEncoder, indent=2, ensure_ascii=False
        )
        return super().form_collection_valid(form_collection)


class DemoFormCollectionView(DemoFormCollectionViewMixin, FormCollectionView):
    pass


class UserCollectionView(DemoFormCollectionViewMixin, EditCollectionView):
    model = get_user_model()
    template_name = 'testapp/form-collection.html'

    def get_object(self, queryset=None):
        user, _ = self.model.objects.get_or_create(username='demo')
        return user


class CompanyCollectionView(DemoFormCollectionViewMixin, SessionFormCollectionViewMixin, EditCollectionView):
    model = Company
    collection_class = CompanyCollection
    template_name = 'testapp/form-collection.html'
    extra_context = {
        'click_actions': 'disable -> submit -> reload !~ scrollToError',
        'force_submission': False,
    }


class CompaniesCollectionView(DemoFormCollectionViewMixin, BulkEditCollectionView):
    model = Company
    collection_class = CompaniesCollection
    template_name = 'testapp/form-collection.html'
    extra_context = {
        'click_actions': 'disable -> submit -> reload !~ scrollToError',
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.session.session_key:
            self.request.session.cycle_key()
        return queryset.filter(created_by=self.request.session.session_key)

    def get_form_collection(self):
        form_collection = super().get_form_collection()
        if self.request.method == 'POST':
            # when posting, assign all instances to the current user
            if not self.request.session.session_key:
                self.request.session.cycle_key()
            created_by = self.request.session.session_key
            for data in form_collection.data:
                data['company']['created_by'] = created_by
        return form_collection

    def form_collection_valid(self, form_collection):
        for holder in form_collection.valid_holders:
            holder['company'].instance.created_by = self.request.session.session_key
        return super().form_collection_valid(form_collection)


class GalleryCollectionView(DemoFormCollectionViewMixin, SessionFormCollectionViewMixin, EditCollectionView):
    model = Gallery
    collection_class = GalleryCollection
    template_name = 'testapp/form-collection.html'
    extra_context = {
        'click_actions': 'disable -> submit -> reload !~ scrollToError',
        'force_submission': False,
    }


demo_css_classes = {
    'default': {'*': {}},
    'bootstrap': {
        '*': {
            'field_css_classes': 'mb-2',
            'fieldset_css_classes': 'border p-3',
            'button_css_classes': 'mt-4',
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


extra_doc_horizontal = """
Here we render a Django Form instance using the template tag with different CSS classes:

.. code-block:: django

	{% render_form form "bootstrap" field_css_classes="row mb-3" label_css_classes="col-sm-3" control_css_classes="col-sm-9" %}

When using the Bootstrap framework, they align the label and the field on the same row rather
than placing them below each other.
"""


urlpatterns = [
    path('', render_suburls),
    # path('success', SuccessView.as_view(), name='form_data_valid'),
    path('complete.native', DemoFormView.as_view(
        form_class=CompleteForm,
        extra_doc=extra_doc_native,
    ), name='complete.native'),
    path('complete.extended', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/extended-form.html',
        extra_doc=extra_doc_extended,
    ), name='complete.extended'),
    path('complete.field-by-field', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/field-by-field.html',
    ), name='complete.field-by-field'),
    path('complete.horizontal', DemoFormView.as_view(
        form_class=CompleteForm,
        extra_doc=extra_doc_horizontal,
    ), name='complete.horizontal'),
    path('address', DemoFormView.as_view(
        form_class=AddressForm,
    ), name='address'),
    path('article', DemoFormView.as_view(
        form_class=ArticleForm,
    ), name='article'),
    path('birthdate.box', DemoFormView.as_view(
        form_class=BirthdateBoxForm,
    ), name='birthdate.box'),
    path('birthdate.calendar', DemoFormView.as_view(
        form_class=BirthdateCalendarForm,
    ), name='birthdate.calendar'),
    path('birthdate.input', DemoFormView.as_view(
        form_class=BirthdateInputForm,
    ), name='birthdate.input'),
    path('birthdate.picker', DemoFormView.as_view(
        form_class=BirthdatePickerForm,
    ), name='birthdate.picker'),
    path('moment.box', DemoFormView.as_view(
        form_class=MomentBoxForm,
    ), name='moment.box'),
    path('moment.calendar', DemoFormView.as_view(
        form_class=MomentCalendarForm,
    ), name='moment.calendar'),
    path('moment.input', DemoFormView.as_view(
        form_class=MomentInputForm,
    ), name='moment.input'),
    path('moment.picker', DemoFormView.as_view(
        form_class=MomentPickerForm,
    ), name='moment.picker'),
    path('booking.box', DemoFormView.as_view(
        form_class=BookingBoxForm,
    ), name='booking.box'),
    path('booking.calendar', DemoFormView.as_view(
        form_class=BookingCalendarForm,
    ), name='booking.calendar'),
    path('booking.picker', DemoFormView.as_view(
        form_class=BookingPickerForm,
    ), name='booking.picker'),
    path('schedule.box', DemoFormView.as_view(
        form_class=ScheduleBoxForm,
    ), name='schedule.box'),
    path('schedule.calendar', DemoFormView.as_view(
        form_class=ScheduleCalendarForm,
    ), name='schedule.calendar'),
    path('schedule.picker', DemoFormView.as_view(
        form_class=SchedulePickerForm,
    ), name='schedule.picker'),
    path('opinion', DemoFormView.as_view(
        form_class=OpinionForm,
    ), name='opinion'),
    path('phone', DemoFormView.as_view(
        form_class=PhoneForm,
    ), name='phone'),
    path('questionnaire', DemoFormView.as_view(
        form_class=QuestionnaireForm,
    ), name='questionnaire'),
    path('simplecontact', DemoFormCollectionView.as_view(
        collection_class=SimpleContactCollection,
        initial={'person': sample_person_data},
    ), name='simplecontact'),
    path('customer', DemoFormCollectionView.as_view(
        collection_class=CustomerCollection,
    ), name='customer'),
    path('contact', DemoFormCollectionView.as_view(
        collection_class=ContactCollection,
        initial={'person': sample_person_data, 'numbers': [{'number': {'phone_number': "+1 234 567 8900"}}]},
    ), name='contact'),
    path('contactlist', DemoFormCollectionView.as_view(
        collection_class=ContactCollectionList,
    ), name='contactlist'),
    path('sortablecontact', DemoFormCollectionView.as_view(
        collection_class=SortableContactCollection,
    ), name='sortablecontact'),
    path('sortablecontactlist', DemoFormCollectionView.as_view(
        collection_class=SortableContactCollectionList,
    ), name='sortablecontactlist'),
    path('intermediatecontactlist', DemoFormCollectionView.as_view(
        collection_class=IntermediateContactCollectionList,
    ), name='intermediatecontactlist'),
    path('upload', DemoFormView.as_view(
        form_class=UploadForm,
    ), name='upload'),
    path('moon', DemoFormView.as_view(
        form_class=MoonForm,
        calendar_renderer_class=MoonCalendarRenderer,
    ), name='moon'),
    path('country', DemoFormView.as_view(
        form_class=CountryForm,
    ), name='country'),
    path('counties', DemoFormView.as_view(
        form_class=CountyForm,
    ), name='counties'),
    path('state', DemoFormView.as_view(
        form_class=StateForm,
    ), name='state'),
    path('states', DemoFormView.as_view(
        form_class=StatesForm,
    ), name='states'),
    path('person', DemoModelFormView.as_view(
        form_class=ModelPersonForm,
        model=PersonModel,
    ), name='person'),
    path('poll', DemoModelFormView.as_view(
        form_class=ModelPollForm,
        model=PollModel,
    ), name='poll'),
    path('pollcollection', DemoFormCollectionView.as_view(
        collection_class=PollCollection,
    ), name='poll'),
    path('company', CompanyCollectionView.as_view(), name='company'),
    path('companies', CompaniesCollectionView.as_view(), name='company'),
    path('user', UserCollectionView.as_view(
        collection_class=UserCollection
    ), name='user'),
    path('userlist', UserCollectionView.as_view(
        collection_class=UserListCollection
    ), name='userlist'),
    path('profile', DemoFormCollectionView.as_view(
        collection_class=ProfileCollection
    ), name='profile'),
    path('blog', DemoModelFormView.as_view(
        form_class=BlogModelForm,
        model=BlogModel,
        template_name='testapp/native-form-tiptap.html'
    ), name='blog'),
    path('advertisement', DemoFormView.as_view(
        form_class=AdvertisementForm,
        #initial={'text': initial_html},
    ), name='advertisement'),
    path('button-actions', DemoFormView.as_view(
        form_class=ButtonActionsForm,
        template_name='testapp/button-actions.html',
        extra_context={'click_actions': 'clearErrors -> disable -> spinner -> submit -> okay(1500) -> proceed !~ enable -> bummer(9999)'},
    ), name='button-actions'),
    path('gallerycollection', GalleryCollectionView.as_view(
    ), name='gallerycollection'),
]
