from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import get_resolver, path, reverse_lazy
from django.utils.module_loading import import_string

from formset.views import FormCollectionView
from formset.utils import FormMixin

from testapp.forms import (SubscribeForm, UploadForm, PersonForm, SelectForm, DoubleFormCollection,
                           TripleFormCollection, NestedCollection, MultipleCollection)
from testapp.views import SubscribeFormView


framework_contexts = {
    None: None,
    'bootstrap': {'field_css_classes': 'mb-2'},
    'bulma': {'field_css_classes': 'mb-2'},
    'foundation': {},
    'tailwind': {'field_css_classes': 'mb-5'},
    'uikit': {'field_css_classes': 'uk-margin-bottom'},
}


def render_startpage(request):
    def not_blacklisted(url):
        blacklist = ['media', 'success']
        for denyurl in blacklist:
            if not url or url.startswith(denyurl):
                return False
        return True

    all_urls = filter(not_blacklisted, (v[0][0][0] for v in get_resolver().reverse_dict.values()))
    context = {
        'all_urls': all_urls,
    }
    template = get_template('index.html')
    return HttpResponse(template.render(context))


urlpatterns = [
    path('', render_startpage),
    path('success', lambda request: HttpResponse('<h1>Form data succesfully submitted</h1>'), name='form_data_valid'),
]
for framework, attrs in framework_contexts.items():
    if framework:
        urlprefix = f'{framework}/'
        extra_context = dict(attrs, framework=framework)
        renderer = import_string(f'formset.renderers.{framework}.FormRenderer')(**attrs)
        SubscribeFormExtended = type('SubscribeForm', (FormMixin, SubscribeForm), {'default_renderer': renderer})
        # PersonFormCollectionClass = type('PersonFormCollection', (PersonFormCollection,), {'default_renderer': renderer})
        DoubleFormCollectionClass = type('DoubleFormCollection', (DoubleFormCollection,), {'default_renderer': renderer})
        TripleFormCollectionClass = type('TripleFormCollection', (TripleFormCollection,), {'default_renderer': renderer})
        NestedCollectionClass = type('NestedCollection', (NestedCollection,), {'default_renderer': renderer})
        MultipleCollectionClass = type('MultipleCollection', (MultipleCollection,), {'default_renderer': renderer})
    else:
        urlprefix = ''
        extra_context = None
        SubscribeFormExtended = type('SubscribeForm', (FormMixin, SubscribeForm), {})
        # PersonFormCollectionClass = PersonFormCollection
        DoubleFormCollectionClass = DoubleFormCollection
        TripleFormCollectionClass = TripleFormCollection
        NestedCollectionClass = NestedCollection
        MultipleCollectionClass = MultipleCollection

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
        path(f'{urlprefix}double', FormCollectionView.as_view(
            collection_class=DoubleFormCollectionClass,
            success_url=reverse_lazy('form_data_valid'),
            template_name='testapp/form-collection.html',
            extra_context=extra_context,
        )),
        # path(f'{urlprefix}personc', FormCollectionView.as_view(
        #     collection_class=PersonFormCollection,
        #     success_url=reverse_lazy('form_data_valid'),
        #     template_name='testapp/form-collection.html',
        #     extra_context=extra_context,
        # )),
        path(f'{urlprefix}triple', FormCollectionView.as_view(
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
        path(f'{urlprefix}multiple', FormCollectionView.as_view(
            collection_class=MultipleCollectionClass,
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
urlpatterns.extend(static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
))
