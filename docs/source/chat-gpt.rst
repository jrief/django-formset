.. _chat-gpt:

============================
A conversation with Chat-GPT
============================

When designing this library, I was unsure on a few descisions I made. One was the HTTP return code
for forms which do not validate, and the other was the design to allow the submission of more than
one form inside a formset. So I asked Chat-GPT and these where the answers:

**Me**:
If the form does not validate on the server, what is the appropriate HTTP status code to send back
to the client?

**Chat GPT**:
If the form does not validate on the server, the appropriate HTTP status code to send back to the
client is 422 Unprocessable Entity. The 422 status code is part of the HTTP standard and is used to
indicate that the server understands the request but is unable to process it because the client has
sent invalid data. In the case of form validation, this could mean that the client has submitted
data that is missing required fields, or contains invalid data in some way.

When the server sends a 422 status code, it should also include a response body that provides
details about the validation errors that were encountered. This response body can be in any format,
but JSON is a common choice.

Sending a 422 status code along with a detailed response body can help the client understand why the
request failed and provide useful information to help the user correct their input.

**Me**:
Is it possible and a good idea to submit more than one form in one request?

**Chat GPT**:
It is technically possible to submit more than one form in one request, but it is generally not a
good idea to do so.

Each HTML form represents a distinct set of data, and submitting multiple forms in one request can
make it difficult to handle the data on the server-side. In addition, submitting multiple forms in
one request can cause conflicts if the forms have overlapping field names or if they have different
requirements for validation.

Instead of submitting multiple forms in one request, it is generally better to combine the data from
the different forms into a single form, or to submit each form separately in its own request. This
approach can help to keep the data organized and make it easier to handle on the server-side.

If you need to submit data from multiple forms together, you can use JavaScript to collect the data
from the different forms and combine it into a single request payload. This approach can be more
complex to implement, but it can help to keep the data organized and reduce conflicts.

**Me**:
In HTML, is it a good idea to invent arbitrary tag names without connecting them to a web component?

**Chat GPT**:
No, it is not a good idea to invent arbitrary tag names in HTML without connecting them to a web
component.

HTML is a standardized language with predefined tag names that have specific meanings and functions.
Using arbitrary tag names that are not recognized by HTML can cause problems with validation,
parsing, and accessibility.

Additionally, if you use arbitrary tag names without a web component, it may confuse other
developers who are trying to understand your code. They may not know what the tag is intended for or
how to use it, which can lead to errors and difficulties in maintaining and updating the code.

If you need custom functionality in your HTML, it's better to use web components, which are designed
to extend the functionality of HTML with custom tags, attributes, and behaviors. This way, your
custom tags will have a clear purpose and be easy to understand and use by other developers.
