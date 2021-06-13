from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic import TemplateView

from testapp.forms import (DefaultMixinForm, BootstrapMixinForm, BulmaMixinForm, FoundationMixinForm,
                           TailwindMixinForm, UploadForm, PersonForm, SelectForm)
from testapp.views import SubscribeFormView


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('formsetify', SubscribeFormView.as_view(template_name='default/formsetify.html'), name='formsetify'),
    path('form-groups', SubscribeFormView.as_view(template_name='default/render_groups.html'), name='form-groups'),
    path('mixin-form', SubscribeFormView.as_view(form_class=DefaultMixinForm, template_name='default/mixin_form.html'), name='mixin-form'),
    path('upload', SubscribeFormView.as_view(form_class=UploadForm, template_name='default/render_groups.html')),
    path('persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='default/render_groups.html')),
    path('select', SubscribeFormView.as_view(form_class=SelectForm, template_name='default/formsetify.html')),
    path('bootstrap/formsetify', SubscribeFormView.as_view(template_name='bootstrap/formsetify.html')),
    path('bootstrap/form-groups', SubscribeFormView.as_view(template_name='bootstrap/render_groups.html')),
    path('bootstrap/form-groups-classes', SubscribeFormView.as_view(template_name='bootstrap/render_groups_with_classes.html')),
    path('bootstrap/mixin-form', SubscribeFormView.as_view(form_class=BootstrapMixinForm, template_name='bootstrap/mixin_form.html')),
    path('bootstrap/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='bootstrap/render_groups.html')),
    path('bootstrap/personb', SubscribeFormView.as_view(form_class=PersonForm, template_name='bootstrap/render_groups_with_classes.html')),
    path('bootstrap/select', SubscribeFormView.as_view(form_class=SelectForm, template_name='bootstrap/render_groups.html')),
    path('bulma/formsetify', SubscribeFormView.as_view(template_name='bulma/formsetify.html')),
    path('bulma/form-groups', SubscribeFormView.as_view(template_name='bulma/render_groups.html')),
    path('bulma/mixin-form', SubscribeFormView.as_view(form_class=BulmaMixinForm, template_name='bulma/mixin_form.html')),
    path('bulma/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='bulma/render_groups.html')),
    path('foundation/formsetify', SubscribeFormView.as_view(template_name='foundation/formsetify.html')),
    path('foundation/form-groups', SubscribeFormView.as_view(template_name='foundation/render_groups.html')),
    path('foundation/mixin-form', SubscribeFormView.as_view(form_class=FoundationMixinForm, template_name='foundation/mixin_form.html')),
    path('foundation/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='foundation/render_groups.html')),
    path('tailwind/formsetify', SubscribeFormView.as_view(template_name='tailwind/formsetify.html')),
    path('tailwind/form-groups', SubscribeFormView.as_view(template_name='tailwind/render_groups.html')),
    path('tailwind/mixin-form', SubscribeFormView.as_view(form_class=TailwindMixinForm, template_name='tailwind/mixin_form.html')),
    path('tailwind/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='tailwind/render_groups.html')),
    path('success', TemplateView.as_view(template_name='default/success.html'), name='form_data_valid'),
]
if settings.DEBUG:
    urlpatterns.extend(static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    ))
