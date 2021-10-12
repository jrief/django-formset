from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView

from formset.views import FormCollectionView
from formset.renderers import bootstrap
from formset.utils import FormMixin

from testapp.forms import SubscribeForm, UploadForm, PersonForm, SelectForm, TripleFormCollection
from testapp.views import SubscribeFormView


class SubscribeFormExtended(FormMixin, SubscribeForm):
    pass


class SubscribeFormExtendedBootstrap(SubscribeFormExtended):
    default_renderer = bootstrap.FormRenderer


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('subscribe.form-groups', SubscribeFormView.as_view(template_name='default/form-groups.html')),
    path('subscribe.form-extended', SubscribeFormView.as_view(form_class=SubscribeFormExtended, template_name='default/form-extended.html')),
    path('subscribe.field-by-field', SubscribeFormView.as_view(template_name='default/field-by-field.html')),
    path('upload', SubscribeFormView.as_view(form_class=UploadForm, template_name='default/form-groups.html')),
    path('persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='default/form-groups.html')),
    path('selectize', SubscribeFormView.as_view(form_class=SelectForm, template_name='default/form-groups.html')),
    path('collection', FormCollectionView.as_view(
        collection_class=TripleFormCollection,
        success_url=reverse_lazy('form_data_valid'),
        template_name='default/form-collection.html'),
    ),
    path('bootstrap/subscribe.form-groups', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='bootstrap/form-groups.html')),
    path('bootstrap/subscribe.form-extended', SubscribeFormView.as_view(form_class=SubscribeFormExtendedBootstrap, template_name='bootstrap/form-extended.html')),
    path('bootstrap/subscribe.form-rows', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='bootstrap/form-rows.html')),
    path('bootstrap/persona.form-groups', SubscribeFormView.as_view(form_class=PersonForm, template_name='bootstrap/form-groups.html')),
    path('bootstrap/persona.form-rows', SubscribeFormView.as_view(form_class=PersonForm, template_name='bootstrap/form-rows.html')),
    path('bootstrap/selectize.form-groups', SubscribeFormView.as_view(form_class=SelectForm, template_name='bootstrap/form-groups.html')),
    path('bulma/subscribe.form', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='bulma/form-groups.html')),
    # path('bulma/formsetify', SubscribeFormView.as_view(template_name='bulma/formsetify.html')),
    # path('bulma/form-groups', SubscribeFormView.as_view(template_name='bulma/render_groups.html')),
    #path('bulma/mixin-form', SubscribeFormView.as_view(form_class=BulmaMixinForm, template_name='bulma/mixin_form.html')),
    # path('bulma/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='bulma/render_groups.html')),
    # path('bulma/selectize', SubscribeFormView.as_view(form_class=SelectForm, template_name='bulma/render_groups.html')),
    path('foundation/subscribe.form', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='foundation/form-groups.html')),
    path('tailwind/subscribe.form', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='tailwind/form-groups.html')),
    path('uikit/subscribe.form', SubscribeFormView.as_view(form_class=SubscribeForm, template_name='uikit/form-groups.html')),
    # path('foundation/formsetify', SubscribeFormView.as_view(template_name='foundation/formsetify.html')),
    # path('foundation/form-groups', SubscribeFormView.as_view(template_name='foundation/render_groups.html')),
    #path('foundation/mixin-form', SubscribeFormView.as_view(form_class=FoundationMixinForm, template_name='foundation/mixin_form.html')),
    # path('foundation/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='foundation/render_groups.html')),
    # path('foundation/selectize', SubscribeFormView.as_view(form_class=SelectForm, template_name='foundation/render_groups.html')),
    # path('tailwind/formsetify', SubscribeFormView.as_view(template_name='tailwind/formsetify.html')),
    # path('tailwind/form-groups', SubscribeFormView.as_view(template_name='tailwind/render_groups.html')),
    #path('tailwind/mixin-form', SubscribeFormView.as_view(form_class=TailwindMixinForm, template_name='tailwind/mixin_form.html')),
    # path('tailwind/persona', SubscribeFormView.as_view(form_class=PersonForm, template_name='tailwind/render_groups.html')),
    # path('tailwind/selectize', SubscribeFormView.as_view(form_class=SelectForm, template_name='tailwind/render_groups.html')),
    path('success', TemplateView.as_view(template_name='default/success.html'), name='form_data_valid'),
]
if settings.DEBUG:
    urlpatterns.extend(static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    ))
