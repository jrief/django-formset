.. _development:


============================
Developing in django-formset
============================

**django-formset** is a 3rd party Django library partially written in Python, TypeScript_ and
`PEGGY.js`_. The last two applications are required for the client part and make up about one third
of the code base.

The code can be found on GitHub_. Please use the issue tracker **only** to report bugs. For
questions and new ideas, please use the discussion board.

.. _TypeScript: https://www.typescriptlang.org/
.. _PEGGY.js: https://peggyjs.org/documentation.html
.. _GitHub: https://github.com/jrief/django-formset

When building this library locally, it therefore is strongly recommended that you install the whole
tool-chain required to build the test application:

.. code-block:: shell

	git clone https://github.com/jrief/django-formset.git
	cd django-formset
	python -m venv .venv
	source .venv/bin/activate
	pip install Django
	pip install -r testapp/requirements.txt
	pip install https://github.com/jrief/django-sphinx-view/archive/refs/heads/main.zip
	pip install --no-deps -e .
	npm install --include=dev
	npm run tag-attributes
	npm run function-code
	npm run tailwindcss
	npm run esbuild
	npm run compilescss
	npm run docscss
	mkdir workdir
	export DJANGO_DEBUG=true
	sphinx-build -M json docs/source build
	testapp/manage.py migrate
	testapp/manage.py runserver

Open http://localhost:8000/ in your browser. This should show the same documentation you're
currently reading.


Setting up and running Tests
============================

Since there is a lot of interaction between the browser and the server, the client is tested using
pytest_ together with Playwright_. The latter is a testing framework to run end-to-end tests using a
headless browser. It must be initialized using:

.. code-block:: shell

	playwright install

Then run the testsuite

.. code-block:: shell

	pytest testapp


.. _pytest: https://pytest-django.readthedocs.io/en/latest/
.. _Playwright: https://playwright.dev/python/docs/intro/


Building the Parsers
====================

The content of the button attribute ``df-click``, and the input field and fieldset attributes
``df-show``, ``df-hide`` and ``df-disable`` are parsed before being evaluated by the code
implementing the web component. This parser is generated using PEGGY and compiles to a pure
TypeScript module through ``npm run tag-attributes``. The grammar describing this proprietary syntax
can be found in ``assets/tag-attributes.pegjs``. The final parser is generated using
``npm run tag-attributes`` and written to ``client/django-formset/tag-attributes.ts``. It then is
imported by the code implementing the web component ``client/django-formset/DjangoFormset.ts``.

Another parse is built to convert Tiptap extensions, so that they can be loaded dynamically. This
parser is generated using ``npm run function-code`` and written to
``client/django-formset/function-code.ts``. It then is imported by the code implementing the web
component ``client/django-formset/RichtextArea.ts``.


Building the Client
===================

The client part consists of a few TypeScript modules which all are compiled and bundled to
JavaScript using ``npm run esbuild``. The default TypeScript compiler used in this project is
esbuild_, which currently is the fastest compiler of its kind.

.. _esbuild: https://esbuild.github.io/

The client can be built in three ways:

.. rubric:: ``npm run esbuild``

This creates a bundle of JavaScript modules. The main entry point is found in file
``formset/static/formset/django-formset.js``. This file only contains the core functionality, ie.
that one, required for web component ``<django-formset>``. The JavaScript modules for all the other
components, such as ``<select is="django-selectize">``, ``<django-dual-selector>``,
``<textarea is="django-richtext">``, etc. are loaded upon demand.

This is the default setting.


.. rubric:: ``npm run esbuild -- --monolith``

This creates one single monolithic JavaScript module, named
``formset/static/formset/django-formset.js``. In some circumstances this might be preferable over
many splitted  modules.


.. rubric:: ``npm run esbuild -- --debug``

This compiles TypeScript to JavaScript without minimizing plus additional `source maps`_. This build
target should be used during development of client side code. 

.. _source maps: https://web.dev/source-maps/


.. rubric:: ``npm run rollup``

This works similar to ``esbuild``. However instead of using the ``esbuild`` compiler it uses
rollup_ + babel_ + terser_.

.. _rollup: https://rollupjs.org/guide/en/
.. _babel: https://babel.dev/docs/en/babel-core
.. _terser: https://terser.org/

I haven't found any compelling reason why to use ``rollup`` instead of ``esbuild``, since building
the bundle takes much longer and the output sizes are comparable. For reasons of code hygiene, one
sample of the unit tests is run using this setup.


Building the Documentation
==========================

Thanks to the django-sphinx-view_ project, the documentation of **django-formset** can be built
using embedded functional forms. During development this is very helpful, because the examples
now sit side-by-side with documentation describing them.

.. _django-sphinx-view: https://noumenal.es/django-sphinx-view/

In order for this to work, please run 

.. code-block:: shell

	make -C docs json
	npm run docscss
	python manage.py runserver

The first command builds the documentation as a set of JSON and Python files. They then are loaded
by the **django-sphinx-view** module.

The second command builds some specially formatted CSS files. They are required, so that Tailwind-,
Bootstrap- and the Furo-themes do not interfere with each other.

The third command starts the Django application with integrated documentation.


Running the Django Test App
===========================

The unit tests and the application used to test the functionality, share a lot of code. In my
opinion this is really important, because when writing code for end users, manual testing is
mandatory. Therefore all unit tests provided with this application have been manually verified.
Otherwise I could not guarantee a user experience which feels natural.
