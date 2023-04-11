from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import include, path

from sphinx_view import DocumentationView

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
    path('', render_landing),
    path('success', lambda request: HttpResponse('<h1>Form data succesfully submitted</h1>'), name='form_data_valid'),
    path('default/', include(('testapp.views', 'default'))),
    path('bootstrap/', include(('testapp.views', 'bootstrap'))),
    path('bulma/', include(('testapp.views', 'bulma'))),
    path('foundation/', include(('testapp.views', 'foundation'))),
    path('tailwind/', include(('testapp.views', 'tailwind'))),
    path('uikit/', include(('testapp.views', 'uikit'))),
    path('docs<path:path>',
        DocumentationView.as_view(
            json_build_dir=Path(settings.BASE_DIR / 'docs/build/json'),
            base_template_name='docs/base.html',
        ),
        name="documentation",
    ),
]
urlpatterns.extend(static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
))
