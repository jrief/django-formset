import os

from django.urls import path
from django.views.i18n import JavaScriptCatalog


use_monolithic_build = os.environ.get('PYTEST_USE_MONOLITHIC_BUILD') == '1'


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(use_monolithic_build=use_monolithic_build)
        return context


def get_javascript_catalog():
    return path(
        'jsi18n/myapp/',
        JavaScriptCatalog.as_view(packages=['formset']),
        name='javascript-catalog',
    )
