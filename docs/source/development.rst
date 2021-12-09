.. _development:


Developing in django-formset
============================

**django-formset** is a library partially written in Python, TypeScript_ and `PEG.js`_. The last
two applications are required for the client part and make up about one quarter of the code base.

The code can be found on GitHub_. Report bugs using the issue tracker, but please ask questions
on the Discussion board.

.. _TypeScript: https://www.typescriptlang.org/
.. _PEG.js: https://peggyjs.org/documentation.html
.. _GitHub: https://github.com/jrief/django-formset

When playing with this library it therefore is strongly recommended that you install the whole
tool-chain required to build the test application:

.. code-block:: shell

	git clone https://github.com/jrief/django-formset.git
	cd django-formset
	python -m venv .venv
	source .venv/bin/activate
	pip install -r testapp/requirements.txt
	pip install --no-deps -e .
	npm install --also=dev
	npm run tag-attributes
	npm run tailwindcss
	npm run build
	testapp/manage.py migrate
	testapp/manage.py runserver

Open http://localhost:8000/ in your browser. There is a long list of forms for all kind of purposes.


Setting up the Tests
--------------------

Since there is a lot of interaction between the browser and the server, the client is tested using
pytest_ together with Playwright_ in order to run end-to-end tests. Playwright is a test-runner
using a headless browser. It must be initialized using:

.. _pytest: https://pytest-django.readthedocs.io/en/latest/
.. _Playwright: https://playwright.dev/python/docs/intro/

.. code-block:: shell

	playwright install

Then run the testsuite

.. code-block:: shell

	pytest testapp


Building the Parser
-------------------

The content of the button attribute ``click``, and the input field and fieldset attributes
``show-if``, ``hide-if`` and ``disable-if`` are parsed before being evaluated by the code
implementing the Web Component. This parser is generated using PEG.js and compiles to a pure
TypeScript module. The grammer describing this proprietary syntax can be found in
``assets/tag-attributes.pegjs``. The final parser is generated using ``npm run tag-attributes``
and written to ``client/django-formset/tag-attributes.ts``. It then is imported by the code
implementing the Web Component ``client/django-formset/DjangoFormset.ts``.


Building the Client
-------------------

The client part consists of a few TypeScript modules which all are compiled and bundled to a single
JavaScript file using ``npm run build``. The default TypeScript compiler used in this project is
esbuild_, which currently is the fastest compiler of its kind. Feel free to use alternative
TypeScript compilers, they will take longer but might build smaller target modules.

.. _esbuild: https://esbuild.github.io/


Running the Django Test App
---------------------------

The unit tests and the application used to test the functionality, share a lot of code. In my
opinion this is really important, because when when writing code for end users, manual testing is
mandatory. Therefore all unit tests provided with this application have been manually tried out.
Otherwise I could not guarantee a user experience which feels right.
