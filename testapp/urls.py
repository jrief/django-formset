from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog

from formset import __version__


def render_landing(request):
    context = {
        'FORMSET_VERSION': __version__,
        'frameworks': [
            'default',
            'bootstrap',
            'bulma',
            'foundation',
            'tailwind',
            'uikit',
        ],
    }
    template = get_template('landing.html')
    return HttpResponse(template.render(context))


urlpatterns = [
    # path('', render_landing),
    path('success', lambda request: HttpResponse('<h1>Form data succesfully submitted</h1>'), name='form_data_valid'),
    path('default/', include(('testapp.views', 'default'))),
    path('bootstrap/', include(('testapp.views', 'bootstrap'))),
    path('bulma/', include(('testapp.views', 'bulma'))),
    path('foundation/', include(('testapp.views', 'foundation'))),
    path('tailwind/', include(('testapp.views', 'tailwind'))),
    path('uikit/', include(('testapp.views', 'uikit'))),
]
if settings.USE_I18N:
    urlpatterns.extend(i18n_patterns(path(
        'jsi18n/',
        cache_page(3600)(JavaScriptCatalog.as_view(packages=['formset'])),
        name='javascript-catalog'
    )))
urlpatterns.extend(static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
))
if 'sphinx_view' in settings.INSTALLED_APPS:
    urlpatterns.append(path('', include(('sphinx_view.urls', 'sphinx-view'))))
