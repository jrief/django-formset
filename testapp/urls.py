from django.contrib import admin
from django.urls import path

from views import SubscribeView, SuccessView, TestView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('form1/', SubscribeView.as_view(template_name='form1.html')),
    path('form2/', SubscribeView.as_view(template_name='form2.html')),
    path('form3/', TestView.as_view(template_name='form3.html')),
    path('form4/', TestView.as_view(template_name='form4.html')),
    path('form5/', TestView.as_view(template_name='form5.html')),
    path('success/', SuccessView.as_view(), name='form_data_valid'),
]
