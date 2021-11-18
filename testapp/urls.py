from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import include, path


def render_landing(request):
    context = {
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
    path('default/', include(('framework', 'default'))),
    path('bootstrap/', include(('framework', 'bootstrap'))),
    path('bulma/', include(('framework', 'bulma'))),
    path('foundation/', include(('framework', 'foundation'))),
    path('tailwind/', include(('framework', 'tailwind'))),
    path('uikit/', include(('framework', 'uikit'))),
]
urlpatterns.extend(static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
))
