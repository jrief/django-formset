.. _uploading:

==========================
Uploading Files and Images
==========================

In traditionally rendered forms, the payload of files to be uploaded is submitted together with the
form data. This approach is not very user friendly, because submitting such a form can take a
considerable amount of time on slow Internet connections. Even worse, if the form does not validate
on the server, that upload must be repeated again. Moreover, if a form contains more than one file
to be uploaded, the maximum size a client can upload to the server must be shared for all of them
[#1]_, [#2]_.

.. _LimitRequestBody: https://httpd.apache.org/docs/2.4/mod/core.html#limitrequestbody
.. _client_max_body_size: http://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size

Therefore **django-formset** handles file uploads asynchronously. This means that the payload of a
file is uploaded to the server as soon as the user opens the file dialog or drags a file on the
area nearby the file input button. While the payload of that file is transferred, the user can fill
out other fields. The uploaded file is stored in a temporary folder on the server. After successful
file upload, a unique and signed handle is returned to the client. On form submission, this handle
then is used to refer to the previously uploaded file inside the temporary folder. If the form
validation passed successfully, that file then is moved to its final destination.

 It allows us to visually upload a file, which means that the
    uploaded payload is pre-submitted and a thumbnailed depiction is rendered. Since the uploaded
    file already waits in a temporary location on the server, the final form submission also is a
    lot faster.




Example
-------

A Django form accepting files for upload can be converted easily to **django-formset**'s
asynchronous file uploads, simply by replacing the widget.

.. django-view:: upload_form
	:view-function: UploadView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'upload-result'})

	from django.forms import forms, fields
	from formset.views import FormView 
	from formset.widgets import UploadedFileInput
	
	class UploadForm(forms.Form):
	    avatar = fields.FileField(
	        label="Avatar",
	        widget=UploadedFileInput,
	        required=True,
	    )

	class UploadView(FormView):
	    form_class = UploadForm
	    template_name = "form.html"
	    success_url = "/success"

Remember, the Django view accepting the form data, must inherit from
:class:`formset.upload.FileUploadMixin`. The class :class:`formset.views.FormView` already derives
from it. No extra endpoint is required to activate this feature.

If an uploaded file contains an image renderable by the browser, that image is resized on the server
and a thumbnail version is returned to the client. For other file types, a symbolic icon is
returned.

.. rubric:: Footnotes

.. [#1] On Apache this parameter is configured through the LimitRequestBody_ directive.
.. [#2] On NGiNX this parameter is configured through the client_max_body_size_ directive.
