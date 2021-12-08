import itertools

from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import get_resolver, path, reverse_lazy
from django.utils.module_loading import import_string

from formset.utils import FormMixin
from formset.views import FormView, FormCollectionView

from testapp.forms.address import AddressForm
from testapp.forms.complete import CompleteForm
from testapp.forms.contact import SimpleContactCollection, ContactCollection, ContactCollectionList
from testapp.forms.customer import CustomerCollection
from testapp.forms.opinion import OpinionForm
from testapp.forms.person import SimplePersonForm, sample_person_data
from testapp.forms.questionnaire import QuestionnaireForm
from testapp.forms.upload import UploadForm


def render_suburls(request):
    all_urls = set(filter(lambda url: url, (v[0][0][0] for v in get_resolver(__name__).reverse_dict.values())))
    context = {
        'framework': request.resolver_match.app_name,
        'all_urls': sorted(all_urls),
    }
    template = get_template('index.html')
    return HttpResponse(template.render(context))


class DemoViewMixin:
    success_url = reverse_lazy('form_data_valid')

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
        context_data.update(**self.get_css_classes())
        return context_data


class DemoFormView(DemoViewMixin, FormView):
    template_name = 'testapp/native-form.html'

    def get_form_class(self):
        form_class = super().get_form_class()
        assert not issubclass(form_class, FormMixin)
        attrs = self.get_css_classes()
        attrs.pop('button_css_classes', None)
        renderer = import_string(f'formset.renderers.{self.framework}.FormRenderer')(**attrs)
        if self.mode != 'native':
            form_class = type(form_class.__name__, (FormMixin, form_class), {'default_renderer': renderer})
        return form_class


class DemoFormCollectionView(DemoViewMixin, FormCollectionView):
    template_name = 'testapp/form-collection.html'

    def get_collection_class(self):
        collection_class = super().get_collection_class()
        attrs = self.get_css_classes()
        attrs.pop('button_css_classes', None)
        collection_class.default_renderer = import_string(f'formset.renderers.{self.framework}.FormRenderer')(**attrs)
        return collection_class


demo_css_classes = {
    'default': {'*': {}},
    'bootstrap': {
        '*': {
            'field_css_classes': 'mb-2',
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
    },
    'bulma': {
        '*': {
            'field_css_classes': 'mb-2',
        },
    },
    'foundation': {},
    'tailwind': {
        '*': {'field_css_classes': 'mb-5'},
    },
    'uikit': {
        '*': {'field_css_classes': 'uk-margin-bottom'},
    },
}


urlpatterns = [
    path('', render_suburls),
    path('address', DemoFormView.as_view(
        form_class=AddressForm,
    ), name='address'),
    path('complete.native', DemoFormView.as_view(
        form_class=CompleteForm,
    ), name='complete.native'),
    path('complete.extended', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/extended-form.html',
    ), name='complete.extended'),
    path('complete.field-by-field', DemoFormView.as_view(
        form_class=CompleteForm,
        template_name='testapp/field-by-field.html',
    ), name='complete.field-by-field'),
    path('complete.horizontal', DemoFormView.as_view(
        form_class=CompleteForm,
    ), name='complete.horizontal'),
    path('simplecontact', DemoFormCollectionView.as_view(
        collection_class=SimpleContactCollection,
        initial={'person': sample_person_data},
    ), name='simplecontact'),
    path('contact', DemoFormCollectionView.as_view(
        collection_class=ContactCollection,
    ), name='contact'),
    path('contactlist', DemoFormCollectionView.as_view(
        collection_class=ContactCollectionList,
    ), name='contactlist'),
    path('customer', DemoFormCollectionView.as_view(
        collection_class=CustomerCollection,
    ), name='customer'),
    path('opinion', DemoFormView.as_view(
        form_class=OpinionForm,
    ), name='opinion'),
    path('questionnaire', DemoFormView.as_view(
        form_class=QuestionnaireForm,
    ), name='questionnaire'),
    path('upload', DemoFormView.as_view(
        form_class=UploadForm,
    ), name='upload'),
]

# this creates permutations of forms to show how to withhold which feedback
withhold_feedbacks = ['messages', 'errors', 'warnings', 'success']
for length in range(len(withhold_feedbacks) + 1):
    for withhold_feedback in itertools.combinations(withhold_feedbacks, length):
        suffix = '.' + ''.join(w[0] for w in withhold_feedback) if length else ''
        urlpatterns.append(
            path(f'withhold{suffix}', DemoFormView.as_view(
                form_class=SimplePersonForm,
                extra_context={'withhold_feedback': ' '.join(withhold_feedback)},
            ))
        )
