.. _faq:

Frequently Asked Questions
==========================

.. rubric:: After clicking on the submit button, nothing happens.

There are various reasons why this can happen:

* Check that the ``<button>``-element contains the attribute ``df-click="submit"``. Note
  that in version 1, ``click`` has been renamed to ``df-click``.
* Open your browser's developer tools, navigate to the "Network" tab and optionally filter by
  "Fetch/XHR" requests. After submission, check if your form data has been submitted to the server.
  If the form does not validate, the server will return a response with status 422. Check the
  contents of the response to see which fields are invalid. Very often the problem is that a field
  is hidden, but the form validation logic requires a value. 
