from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from testapp.forms import DefaultMixinForm, BootstrapMixinForm, FoundationMixinForm, TailwindMixinForm
from testapp.views import SubscribeFormView


urlpatterns = [
    path('admin', admin.site.urls),
    path('native', SubscribeFormView.as_view(template_name='default/native.html')),
    path('formsetify', SubscribeFormView.as_view(template_name='default/formsetify.html')),
    path('form-groups', SubscribeFormView.as_view(template_name='default/render_groups.html')),
    path('mixin-form', SubscribeFormView.as_view(form_class=DefaultMixinForm, template_name='default/mixin_form.html')),
    path('bootstrap/formsetify', SubscribeFormView.as_view(template_name='bootstrap/formsetify.html')),
    path('bootstrap/form-groups', SubscribeFormView.as_view(template_name='bootstrap/render_groups.html')),
    path('bootstrap/form-groups-classes', SubscribeFormView.as_view(template_name='bootstrap/render_groups_with_classes.html')),
    path('bootstrap/mixin-form', SubscribeFormView.as_view(form_class=BootstrapMixinForm, template_name='bootstrap/mixin_form.html')),
    path('foundation/formsetify', SubscribeFormView.as_view(template_name='foundation/formsetify.html')),
    path('foundation/form-groups', SubscribeFormView.as_view(template_name='foundation/render_groups.html')),
    path('foundation/mixin-form', SubscribeFormView.as_view(form_class=FoundationMixinForm, template_name='foundation/mixin_form.html')),
    path('tailwind/formsetify', SubscribeFormView.as_view(template_name='tailwind/formsetify.html')),
    path('tailwind/form-groups', SubscribeFormView.as_view(template_name='tailwind/render_groups.html')),
    path('tailwind/mixin-form', SubscribeFormView.as_view(form_class=TailwindMixinForm, template_name='tailwind/mixin_form.html')),
    path('success', TemplateView.as_view(template_name='default/success.html'), name='form_data_valid'),
]
