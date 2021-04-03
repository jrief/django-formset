from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from testapp.forms import SubscribeMixinForm, BootstrapMixinForm, TailwindMixinForm
from testapp.views import SubscribeView


urlpatterns = [
    path('admin', admin.site.urls),
    path('native', SubscribeView.as_view(template_name='default/native.html')),
    path('formsetify', SubscribeView.as_view(template_name='default/formsetify.html')),
    path('form-groups', SubscribeView.as_view(template_name='default/render_groups.html')),
    path('mixin-form', SubscribeView.as_view(form_class=SubscribeMixinForm, template_name='default/mixin_form.html')),
    path('bootstrap/formsetify', SubscribeView.as_view(template_name='bootstrap/formsetify.html')),
    path('bootstrap/form-groups', SubscribeView.as_view(template_name='bootstrap/render_groups.html')),
    path('bootstrap/form-groups-classes', SubscribeView.as_view(template_name='bootstrap/render_groups_with_classes.html')),
    path('bootstrap/mixin-form', SubscribeView.as_view(form_class=BootstrapMixinForm, template_name='bootstrap/mixin_form.html')),
    path('foundation/formsetify', SubscribeView.as_view(template_name='foundation/formsetify.html')),
    path('foundation/form-groups', SubscribeView.as_view(template_name='foundation/render_groups.html')),
    path('tailwind/formsetify', SubscribeView.as_view(template_name='tailwind/formsetify.html')),
    path('tailwind/form-groups', SubscribeView.as_view(template_name='tailwind/render_groups.html')),
    path('tailwind/mixin-form', SubscribeView.as_view(form_class=TailwindMixinForm, template_name='tailwind/mixin_form.html')),
    path('success', TemplateView.as_view(template_name='default/success.html'), name='form_data_valid'),
]
