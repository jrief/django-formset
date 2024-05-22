from django.urls import path
from django.views.i18n import JavaScriptCatalog


def get_javascript_catalog():
    return path(
        'jsi18n/myapp/',
        JavaScriptCatalog.as_view(packages=['formset']),
        name='javascript-catalog',
    )
