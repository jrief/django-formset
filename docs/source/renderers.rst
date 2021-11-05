.. _renderers:

**To be documented**

Form Renderers
==============


Usage
=====


.. code-block:: python

	from django.forms import forms, fields
	
	class SubscribeForm(forms.Form):
	    last_name = fields.CharField(
	        label="Last name",
	        min_length=2,
	        max_length=50,
	    )
	
	    # ... more fields


This Form must be controlled by a special View class. 


.. code-block:: python

	from django.urls import path
	from formset.views import FormView
	
	from .myforms import SubscribeForm
	
	
	urlpatterns = [
	    ...
	    path('subscribe', FormView.as_view(
	        form_class=SubscribeForm,
	        template_name='my-subscribe-form.html',
	        success_url='/success',
	    )),
	    ...
	]
