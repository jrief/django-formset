from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path, reverse_lazy
from django.utils.module_loading import import_string
from django.views.generic import TemplateView

from formset.views import FormCollectionView
from formset.utils import FormMixin

from testapp.forms import SubscribeForm, UploadForm, PersonForm, SelectForm, TripleFormCollection, NestedCollection, ListCollection
from testapp.views import SubscribeFormView


framework_contexts = {
    None: None,
    'bootstrap': {'field_css_classes': 'mb-2'},
    'bulma': {'field_css_classes': 'mb-2'},
    'foundation': {},
    'tailwind': {'field_css_classes': 'mb-5'},
    'uikit': {'field_css_classes': 'uk-margin-bottom'},
}

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('success', lambda request: HttpResponse('<h1>Form data succesfully submitted</h1>'), name='form_data_valid'),
]
for framework, attrs in framework_contexts.items():
    if framework:
        urlprefix = f'{framework}/'
        extra_context = dict(attrs, framework=framework)
        renderer = import_string(f'formset.renderers.{framework}.FormRenderer')(**attrs)
        SubscribeFormExtended = type('SubscribeForm', (FormMixin, SubscribeForm), {'default_renderer': renderer})
        TripleFormCollectionClass = type('TripleFormCollection', (TripleFormCollection,), {'default_renderer': renderer})
        NestedCollectionClass = type('NestedCollection', (NestedCollection,), {'default_renderer': renderer})
        ListCollectionClass = type('ListCollection', (ListCollection,), {'default_renderer': renderer})
    else:
        urlprefix = ''
        extra_context = None
        SubscribeFormExtended = type('SubscribeForm', (FormMixin, SubscribeForm), {})
        TripleFormCollectionClass = TripleFormCollection
        NestedCollectionClass = NestedCollection
        ListCollectionClass = ListCollection

    urlpatterns.extend([
        path(f'{urlprefix}subscribe.native-form', SubscribeFormView.as_view(
            form_class=SubscribeForm,
            template_name='testapp/native-form.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}subscribe.extended-form', SubscribeFormView.as_view(
            form_class=SubscribeFormExtended,
            template_name='testapp/extended-form.html',
            extra_context={'framework': framework},
        )),
        path(f'{urlprefix}subscribe.field-by-field', SubscribeFormView.as_view(
            template_name='testapp/field-by-field.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}upload', SubscribeFormView.as_view(
            form_class=UploadForm,
            template_name='testapp/native-form.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}persona', SubscribeFormView.as_view(
            form_class=PersonForm,
            template_name='testapp/native-form.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}selectize', SubscribeFormView.as_view(
            form_class=SelectForm,
            template_name='testapp/native-form.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}collection', FormCollectionView.as_view(
            collection_class=TripleFormCollectionClass,
            success_url=reverse_lazy('form_data_valid'),
            template_name='testapp/form-collection.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}nested', FormCollectionView.as_view(
            collection_class=NestedCollectionClass,
            success_url=reverse_lazy('form_data_valid'),
            template_name='testapp/form-collection.html',
            extra_context=extra_context,
        )),
        path(f'{urlprefix}list', FormCollectionView.as_view(
            collection_class=ListCollectionClass,
            success_url=reverse_lazy('form_data_valid'),
            template_name='testapp/form-collection.html',
            extra_context=extra_context,
        )),
    ])
urlpatterns.append(
    path('bootstrap/subscribe.form-rows',
        SubscribeFormView.as_view(form_class=SubscribeForm,
        template_name='bootstrap/form-rows.html',
    ))
)

if settings.DEBUG:
    urlpatterns.extend(static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    ))
