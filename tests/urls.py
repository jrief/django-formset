from django.urls import path

from views import SubscribeView, SuccessView, TestView


urlpatterns = [
    path(r'form1/', SubscribeView.as_view(template_name='form1.html')),
    path(r'form2/', SubscribeView.as_view(template_name='form2.html')),
    path(r'form3/', TestView.as_view(template_name='form3.html')),
    path(r'form4/', TestView.as_view(template_name='form4.html')),
    path(r'form5/', TestView.as_view(template_name='form5.html')),
    path(r'success/', SuccessView.as_view(), name='form_data_valid'),
]
