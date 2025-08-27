.. _contributing:

===========================
Contributing to the Project
===========================

* Please ask question on the `discussion board`_.
* Ideas for new features shall be discussed on that board as well.
* The `issue tracker`_ must *exclusively* be used to report bugs.
* Except for very small fixes (typos etc.), do not open a pull request without an issue.

.. _discussion board: https://github.com/jrief/django-formset/discussions/
.. _issue tracker: https://github.com/jrief/django-formset/issues


Writing Code
============

Before hacking into the code, adopt your IDE to respect the projects's `.editorconfig`_ file.

.. _.editorconfig: https://editorconfig.org/

When installing from GitHub, you *must* build the project from scratch as described in
section :ref:`development`.


Reporting Bugs
==============

For me it often is very difficult to comprehend why this library does not work with *your* project.
Therefore whenever you want to report a bug, **report it in a way so that I can reproduce it**.

**Checkout the code, build the client and run the demo** as described in the previous section.
Every feature offered by **django-formset** is implemented in the demo named ``testapp``.
If you can reproduce the bug there, report it. **Otherwise check why your application behaves
differently**.

If you have a special setup which triggers a bug, clone this project and rebuild an example in
``testapp``, so that I can run that sample in a reproducible way.


Adding new Features
===================

If you want to add a new feature to **django-formset**, please first describe your intention on the
discussion board. It will save you and me hours of wasted work, **because I will not merge
unsolicited pull requests**.

*Don't hide yourself*: I will not accept large pull requests from anonymous users, so please publish
an email address in your GitHub's profile. Reason is that when refactoring the code, I must be
able to contact the initial author of a feature not added by myself. I also will not accept large
pull requests from unsigned commits or developers who can't be traced back to a natural person.

Don't be offended, if I don't respond immediately. I have many projects on GitHub which all require
their maintenance share. Feel free to invite me to conferences or ping me on Twitter_, LinkedIn_ or
Mastodon_.

.. _Twitter: https://twitter.com/jacobrief
.. _LinkedIn: https://www.linkedin.com/in/jacob-rief-27884016a/
.. _Mastodon: https://fosstodon.org/@jrief

If you add a new feature, there must be working example in ``testapp``. Doing so has three benefits:

* I can understand way better what it does and how that new feature works. This increases the
  chances of being accepted and merged.
* You can use that same code to adopt the test suite.
* Everybody can manually test, how that feature looks and feels in various CSS frameworks.

*Remember*: For UI-centric applications such as this one, where the client- and server-side are
strongly entangled with each other, I prefer end-to-end tests way more rather than unit tests.
Reason is, that otherwise I would have to mock the interfaces, which itself is error-prone and
additional work.


Quoting
=======

Please follow these rules when quoting strings:

* A string intended to be read by humans shall be quoted using double quotes: ``"…"``.
* An internal string, such as dictionary keys, etc. (and thus usually not intended to be read by
  humans), shall be quoted using single quotes: ``'…'``. This makes it easier to determine if we
  have to extra check for wording.

There is a good reason to follow this rule: Strings intended for humans, sometimes contain
apostrophes, for instance ``"This is John's profile"``. By using double quotes, those apostrophes
must not be escaped. On the other side whenever we write HTML, we have to use double quotes for
parameters, for instance ``'<a href="https://example.org">Click here!</a>'``. By using single
quotes, those double quotes do not have to be escaped.


Lists versus Tuples
===================

Unfortunately in Django and Python, `we developers far too often
<https://groups.google.com/g/django-developers/c/h4FSYWzMJhs>`_ intermixed lists and tuples without
being aware of their intention. Therefore please follow this rule:

Always use lists, if there is a theoretical possibility that someday, someone might add another
item. Therefore ``list_display``, ``list_display_links``, ``fields``, etc. must always be lists.

Always use tuples, if the number of items is restricted by nature, and there isn't even a
theoretical possibility of being extended.

Example:

.. code-block:: python

	color = ChoiceField(
	    label="Color",
	    choices=[('ff0000', "Red"), ('00ff00', "Green"), ('0000ff', "Blue")],
	)

A ``ChoiceField`` must provide a list of choices. Attribute ``choices`` must be a list because
it is eligible for extension. Its inner items however must be tuples, because they can exlusively
containin the choice value and a human readable label. Here we also intermix single with double
quotes to distinguish strings intended to be read by the machine versus a human.


Indentation
===========

Please use spaces instead of tabs for indentation of Python code. The number of spaces is four.
For HTML, CSS and JavaScript files, please use one tab for indentation. This allows developers to
adopt the indentation level to their personal preferences.

When indenting HTML code, please use two separate independent indentation levels, one for the HTML
code and one for the Django template control structures, such as ``{% for … %}`` or ``{% if … %}``.

.. code-block:: html

	<div class="container">
	  <div class="row">
	{% for col in columns %}
	    <div class="col">
	  {% if col.header %}
	      <h2>{{ col.header }}</h2>
	  {% else %}
	      <p>{{ col.content }}</p>
	  {% endif %}
	    </div>
	{% endfor %}
	  </div>
	</div>

This assures that the rendered HTML code is always indented correctly. It also makes it easier to
review, because the indentation level of the control structures does not depend on the DOM
structure.
