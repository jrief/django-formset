from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from views import SubscribeView


urlpatterns = [
    path('admin', admin.site.urls),
    path('formsetify', SubscribeView.as_view(template_name='default/formsetify.html')),
    path('form-groups', SubscribeView.as_view(template_name='default/render_groups.html')),
    path('bootstrap/formsetify', SubscribeView.as_view(template_name='bootstrap/formsetify.html')),
    path('bootstrap/form-groups', SubscribeView.as_view(template_name='bootstrap/render_groups.html')),
    path('bootstrap/form-groups-classes', SubscribeView.as_view(template_name='bootstrap/render_groups_with_classes.html')),
    path('success', TemplateView.as_view(template_name='default/success.html'), name='form_data_valid'),
]
