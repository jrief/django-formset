from django.urls import path

from views import SubscribeView, SuccessView


urlpatterns = [
    path(r'form1/', SubscribeView.as_view(template_name='tests/form1.html')),
    path(r'form2/', SubscribeView.as_view(template_name='tests/form2.html')),
    path(r'success/', SuccessView.as_view(), name='form_data_valid'),
]
