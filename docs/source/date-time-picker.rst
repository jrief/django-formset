

.. _datetime-picker:

Date-Time Picker Widget
=======================

.. django-view:: blog2_form

    from django.forms import fields, forms
    from formset.widgets import DateTimePicker

    class Blog2Form(forms.Form):
        publish_date = fields.DateTimeField(widget=DateTimePicker)


.. django-view:: blog2_view
	:view-function: Blog2View.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'blog-extra-result'}, form_kwargs={'auto_id': 'be_id_%s'})
	:hide-code:

	class Blog2View(CalendarResponseMixin, FormView):
	    form_class = Blog2Form
	    template_name = "form.html"
	    success_url = "/success"


.. _date-picker:

Date Picker Widget
==================

.. django-view:: blog_form

    from django.forms import fields, forms
    from formset.widgets import DatePicker, DateTimePicker

    class BlogForm(forms.Form):
        publish_date = fields.DateField(widget=DatePicker)

.. django-view:: blog_view
	:caption: BlogView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'blog-result'}, form_kwargs={'auto_id': 'bl_id_%s'})
	:hide-code:

	from formset.calendar import CalendarResponseMixin 
	from formset.views import FormView 

	class BlogView(CalendarResponseMixin, FormView):
	    form_class = BlogForm
	    template_name = "form.html"
	    success_url = "/success"
