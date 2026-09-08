.. _geographic-data:

====================
Edit Geographic Data
====================

.. versionadded:: 2.4

In order to edit the geographic data structures, Django offers a `world-class geographic web
framework`_. This is fine, as long as you need to edit one specific geographic data structure, such
as a single polygon or a single point. However, sometimes we want to edit multiple geographic
data structures inside the same map canvas. In GeoDjango we currently have to edit them one by one,
using an explicit map for each geographic data structure. This sometimes may be inconvenient.

In **django-formset**, we can use a special widget to display a map canvas and configure it so that
it can be used to edit multiple geographic data structures at once. They optionally can be of
different type. In addition to that, we can attach zero to many customized form dialogs to each of
those geographic editor components, allowing to add arbitrary information to each of them. This data
then is exported as GeoJSON according to the specification RFC-7946_. This allows us to store the
edited geographic information in our database using a JSONField_. It also prevents us from having to
install GIS extensions, such as PostGIS_ or SpatiaLite_ to our databases, and still be able to edit
geographic data structures in a convenient way.

For this purpose, **django-formset** offers:

* A special model field :class:`formset.modelfields.geomap.GeoMapField`.
* A special form field :class:`formset.formfields.geomap.GeoMapField`.
* A special widget class :class:`formset.widgets.geomap.GeoMapWidget` to create a customized
  geographic editor component. This widget can be configured to edit multiple different geographic
  data structures using one of these controls:

  * A :class:`formset.geomap.controls.PointEditor` to edit multiple geographic points.
  * A :class:`formset.geomap.controls.PolylineEditor` to edit multiple geographic line strings.
  * A :class:`formset.geomap.controls.PolygonEditor` to edit multiple geographic polygons.
  * A :class:`formset.geomap.controls.MultiPolygonEditor` to edit multiple geographic
    multi-polygons.

Each of those geographic control elements can optionally attach customized form dialogs. Read below
for details.

.. _world-class geographic web framework: https://docs.djangoproject.com/en/stable/ref/contrib/gis/
.. _RFC-7946: https://datatracker.ietf.org/doc/html/rfc7946
.. _JSONField: https://docs.djangoproject.com/en/stable/ref/models/fields/#jsonfield
.. _PostGIS: https://postgis.net/
.. _SpatiaLite: https://www.gaia-gis.it/fossil/libspatialite/index


Simple Geographic Map Editor
============================

This example shows how to use the form field for a geographic map together with the widget class
:class:`formset.widgets.geomap.GeoMapWidget` to edit geographic points.

.. django-view:: simple_point_form
	:caption: form.py

	from django.forms.forms import Form
	from formset.formfields.geomap import GeoMapField
	from formset.geomap.controls import PointEditor
	from formset.widgets.geomap import GeoMapWidget
	
	class SimplePointForm(Form):
	    map = GeoMapField(
	        label="Map",
	        widget=GeoMapWidget(
	            controls_topleft=[
	                PointEditor(max_markers=3),
	            ],
	        ),
	    )

.. django-view:: simple_point_view
	:view-function: GeoMapView.as_view(form_class=geographic_data.SimplePointForm, extra_context={'framework': 'bootstrap', 'pre_id': 'simple-point-result'}, form_kwargs={'auto_id': 'sp_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class GeoMapView(FormView):
	    template_name = "form.html"
	    success_url = "/success"

Here, as control element we only allow a ``PointEditor``. By adding the attribute ``max_markers=3``,
we limit the number of addable points to three. By clicking on the marker button on the upper left
side of the map canvas, the user can start dragging a marker to a position of his choice. The user
can remove this marker again, by clicking on the marker and select the trash symbol appearing inside
the popup. Markers can be moved to a new position by simply dragging them.


Geographic Data Structures of Different Types
=============================================

Since the ``map`` field is a GeoJSON data structure, it can contain multiple geographic data
structures of different types. In this example we allow the user to add points, polylines, polygons
and multipolygons to the map canvas. The user can add as many of them as he wants.

.. django-view:: multiple_geodata_form
	:view-function: GeoMapView.as_view(form_class=geographic_data.MultiGeoDataForm, extra_context={'framework': 'bootstrap', 'pre_id': 'multi-geodata-result'}, form_kwargs={'auto_id': 'mgd_id_%s'})
	:caption: form.py

	from django.forms.forms import Form
	from formset.formfields.geomap import GeoMapField
	from formset.geomap.controls import PolylineEditor, PolygonEditor, MultiPolygonEditor
	from formset.widgets.geomap import GeoMapWidget
	
	class MultiGeoDataForm(Form):
	    map = GeoMapField(
	        label="Map",
	        widget=GeoMapWidget(
	            controls_topleft=[
	                [PointEditor(), PolylineEditor()],
	                [PolygonEditor(), MultiPolygonEditor()],
	            ],
	        ),
	    )

Here we use four control elements, ``PointEditor``, ``PolylineEditor``, ``PolygonEditor`` and
``MultiPolygonEditor``. All four of them are placed in to upper left corner of the map canvas but
other configurations are possible by using the parameters ``controls_topright``,
``controls_bottomleft`` and ``controls_bottomright``. Control buttons can be grouped together by
putting them inside a list, which leaves a small space between the two groups.

The polylines and polygons can be edited by dragging their vertex markers. Each vertex has a halfway
marker, which allows to add a new vertex in between two existing vertices. With a short click on an
existing vertex edge, the adjacent vertices are merged. When clicking on a marker, polyline or
polygon, a popup appears with a trash button to remove that entity.

A multipolygon can be used to represent a polygon with holes. The outer polygon and the inner
polygons are represented as separate polygons inside the same data structure. In order to add a new
separate polygon to a multipolygon, a user must first click on the polygon which opens the popup,
then as a second step, he must click on the "Add Polygon" button.


Custom Marker Symbols
=====================

The default marker symbol for the ``PointEditor`` is a well known blue marker. In some occasions
however, we might want to replace it with a custom marker symbol of our choice. In this example we
create a map to edit the position of churches using the same ``PointEditor`` as above. In Leaflet,
the marker symbol is specified through a dictionary containing the keys ``iconUrl``,
``iconSize``, ``iconAnchor`` and ``popupAnchor``. Please refer to the Leaflet documentation for
details on these attributes. In this example we create a special JSON file located in a Django
templates folder starting with ``geomap/markers``.

.. code-block:: django
	:caption: geomap/markers/church.json

	{% load static %}
	{
	    "iconUrl": "{% static 'testapp/geomap-markers/church.svg' %}",
	    "iconSize": [32, 32],
	    "iconAnchor": [16, 35],
	    "popupAnchor": [0, -28]
	}

The name of that JSON template file refers to the parameter ``identifier`` passed to the
``PointEditor`` control element, which is set to ``church`` in this example.

.. django-view:: churches_map_form
	:view-function: GeoMapView.as_view(form_class=geographic_data.ChurchesMapForm, extra_context={'framework': 'bootstrap', 'pre_id': 'churches-map-result'}, form_kwargs={'auto_id': 'cf_id_%s'})
	:caption: form.py

	class ChurchesMapForm(Form):
	    map = GeoMapField(
	        label="Map of Churches",
	        widget=GeoMapWidget(
	            controls_topright=[
	                PointEditor(
	                    identifier='church',
	                    add_button_icon='testapp/icons/add-church-marker.svg',
	                ),
	            ],
	        ),
	    )

Here we move the control button into the upper right corner and also replace the symbol with a
custom SVG icon using the parameter ``add_button_icon`` by specifying a path to a file located in a
Django templates folder.


Extend with Custom Form Dialogs
===============================

Since **django-formset** allows to nest forms inside each other, we can attach a custom form dialog
to any of the existing geometry editors. Say that we want to name each church and add a maximum
number of visitors together with a short description to each of the given geometry structures. For
this purpose we create a new form class:


.. django-view:: church_dialog_form
	:caption: dialog_form.py

	from django.forms.fields import CharField, IntegerField
	from formset.formfields.richtext import RichTextField
	from formset.geomap.dialogs import GeoMapDialogForm
	
	class ChurchDetailForm(GeoMapDialogForm):
	    title = "Edit Church Details"
	    extension = 'church_details'
	    properties_map = {
	        'name': 'name',
	        'max_visitors': 'max_visitors',
	        'description': 'description',
	    }
	    icon = 'testapp/icons/users.svg'

	    name = CharField(max_length=100)
	    max_visitors = IntegerField()
	    description = RichTextField(required=False)

This dialog form can be attached to the ``PointEditor`` control element. The attribute
``extension`` is used to identify the ``properties`` record in the GeoJSON data structure. The
attribute ``properties_map`` is used to map the form fields to the corresponding keys in the
``properties`` structure. The attribute ``icon`` is used to specify a custom icon for the dialog
form. This icon is displayed in the popup of the marker. The above form then can be rewritten as:


.. code-block:: python
	:emphasize-lines: 9

	class ChurchesMapForm(Form):
	    map = GeoMapField(
	        label="Map of Churches",
	        widget=GeoMapWidget(
	            controls_topright=[
	                PointEditor(
	                    identifier='church',
	                    add_button_icon='testapp/icons/add-church-marker.svg',
	                    dialog_forms=[ChurchDetailForm()],
	                ),
	            ],
	        ),
	    )

Here we replace the default marker symbol against an SVG file of our choice. This alternative marker
is loaded as static file. We also replace the control button with a custom SVG icon and move it into
the upper right corner of the map canvas. The user can add as many church markers as he wants.

The last attribute to our ``PointEditor`` control is the ``dialog_forms`` attribute. This allows to
attach one or more custom form dialogs to each of the markers. In this example we attach a single
form dialog, which allows us to edit the name, the maximum number of visitors for each church
together with a short description using richtext. When the user clicks on the church marker, the
popup now contains an extra button to open a dialog with our ``ChurchCapacityForm`` as declared
above.

On submission, the content of the ``map`` field is exported as GeoJSON, where each marker contains
a record named ``properties`` with a sub record named ``capacity``. That sub record contains the
values of the fields ``name``, ``max_visitors`` and ``description`` as entered by the user.


Geometry Map as Model Form Field
================================

In this example we put all of the above geometry editors together and store the content of the
edited map in a model field inside the database.

.. code-block:: python
	:caption: models.py

	from django.db import models
	from formset.modelfields.geomap import GeoMapField

	class Church(models.Model):
	    map = GeoMapField(
	        verbose_name="Map of Churches",
	        null=True,
	        blank=True,
	    )

Out of this Django model, we can create a model form class. The only part when now have to configure
is the widget for the ``map`` field.

.. django-view:: church_model_form
	:caption: forms.py
	:hide-view:

	from django.forms.models import ModelForm
	from testapp.models import ChurchModel

	class ChurchModelForm(ModelForm):
	    class Meta:
	        model = ChurchModel
	        fields = ['map']
	        widgets = {
	            'map': GeoMapWidget(
	                controls_bottomleft=[
	                    PointEditor(),
	                    PolylineEditor(),
	                    PolygonEditor(),
	                    MultiPolygonEditor(),
	                ],
	                controls_topright=[
	                    PointEditor(
	                        identifier='church',
	                        add_button_icon='testapp/icons/add-church-marker.svg',
	                        dialog_forms=[ChurchDetailForm()],
	                    ),
	                ],
	                attrs={'style': 'height: 450px;'},
	            ),
	        }

.. django-view:: church_edit_view
	:view-function: ChurchEditView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'church-edit-result'}, form_kwargs={'auto_id': 'ce_id_%s'})
	:hide-code:

	from django.views.generic import UpdateView
	from formset.views import FormViewMixin
	from testapp.demo_helpers import SessionModelFormViewMixin

	class ChurchEditView(SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = ChurchModel
	    form_class = ChurchModelForm
	    template_name = 'form.html'
	    success_url = '/success'

.. note:: After submission, the geographic data is stored in the database. Therefore after reloading
	this page, the same content will reappear in the map canvas representing the field.


Rendering the GeoJSON Data Structure
------------------------------------

Until now we have used the ``GeoMapWidget`` to edit geographic data structures and store its content
as GeoJSON. However, we sometimes might want to just represent this structure on a map canvas
outside of a ``<django-formset>``-element and without the possibility to edit it. For this purpose,
**django-formset** offers a special web component named ``<geomap-renderer>``. This component is not
part of the **django-formset** ecosystem and must be loaded separately. It can be used to render a
GeoJSON data structure created by the editors described here.

The GeoJSON specification allows to keep arbitrary data inside the ``properties`` data structure of
each geographic ``Feature``. Up to here, we have stored the content of the configured dialog form
editors inside this ``properties`` record. When rendering this GeoJSON data structure, we need a way
to transform this data to be displayed inside a Leaflet tooltip and/or a popup. For this purpose,
**django-formset** uses the special templates ``geomap/tooltips/{identifier}.json``,
``geomap/tooltips/{identifier}.html``, ``geomap/popups/{identifier}.json`` and
``geomap/popups/{identifier}.html`` to render the content of the configured dialog form editor(s).
The attribute ``identifier`` is the string used to identify the given geometry editor. Template
files ending with ``.json`` are used to configure the ``PopupOptions`` and ``TooltipOptions`` of the
Leaflet popup and tooltip. Refer to the Leaflet documentation for details on the available options.
Template files ending with ``.html`` are used to render the content of the dialog form editor as
HTML. This then is the a human readable content shown inside each Leaflet popup or tooltip
respectively.

In this example we want to render the content of the ``ChurchDetailForm`` dialog form editor as HTML
inside a Leaflet popup. In addition to this, we also want to render the name of the church inside a
Leaflet tooltip. For this purpose, we prepare these Django template files:

.. code-block:: json
	:caption: geomap/tooltips/church.json

	{
	  "offset": [-1, -30],
	  "direction": "top"
	}

.. code-block:: django
	:caption: geomap/tooltips/church.html

	<strong>{{ church_details.name }}</strong>

.. code-block:: django
	:caption: geomap/popups/church.html

	{% load richtext %}
	<h3>Name: {{ church_details.name }}</h3>
	<p>Capacity: {{ church_details.max_visitors }}</p>
	{% render_richtext church_details.description %}

With these templates, we now can display the content of the ``map`` field using our GeoJSON
renderer. For this purpose, **django-formset** offers a special templatetag named
``geomap_renderer``. This templatetag can be used in any Django template and doesn't have to be
embedded inside a ``<django-formset>``. 

.. code-block:: django

	{% load static geojson_tags %}
	<script src="{% static 'formset/js/geojson-renderer.js' %}" type="module"></script>
	…
	{% render_geojson map_data filter="feature?.id?.startsWith('church:')" style="height: 500px;" %}

When rendering this template, the context variable ``map_data`` contains the GeoJSON data structure.

Since this data structure can contain multiple geographic data structures of different type, we use
the optional parameter ``filter`` to restrict the features to be rendered to only churches. In this
example, we only want to render the features which have an ``id`` starting with ``church:``. The
filter must be a valid JavaScript expression. The variable ``feature`` is the current feature being
processed. If unset or invalid, all features from the GeoJSON data structure will be rendered.

.. django-view:: church_detail_view
	:view-function: ChurchDetailView.as_view()
	:hide-code:

	from django.views.generic.base import TemplateResponseMixin
	from django.views.generic import View
	from testapp.demo_helpers import SessionModelFormViewMixin

	class ChurchDetailView(SessionModelFormViewMixin, TemplateResponseMixin, View):
	    template_name = 'testapp/church-detail.html'
	
	    def get(self, request, *args, **kwargs):
	        object = self.get_object(queryset=ChurchModel.objects.all())
	        context = {'map_data': object.map}
	        return self.render_to_response(context)

.. note:: This map is not part of a form and hence not editable. The geographic data shown here has
	been retrieved from the database. It is saved whenever the current user submits the form for the
	model field shown in the previous example.


Alternative Map Tiles
=====================

The map canvas is rendered using the Leaflet_ JavaScript library. By default, the map uses the
OpenStreetMap_ tile server. However, the map can be configured to use any other tile server. For
example, we can use the `basemap.at`_ tile server by adding the following attributes to
the ``GeoMapWidget``:

.. django-view:: alternative_tiles_form
	:view-function: GeoMapView.as_view(form_class=geographic_data.AlternativeTilesForm, extra_context={'framework': 'bootstrap', 'pre_id': 'alternative-tiles-result'}, form_kwargs={'auto_id': 'at_id_%s'})

	class AlternativeTilesForm(Form):
	    map = GeoMapField(
	        label="Map",
	        widget=GeoMapWidget(
	            url_template='https://maps.wien.gv.at/basemap/geolandbasemap/normal/google3857/{z}/{y}/{x}.png',
	            tile_layer_options={
	                'tileSize': 512,
	                'zoomOffset': -1,
	                'attribution': '&copy; <a href="http://basemap.at">Basemap.at</a>',
	                'detectRetina': True,
	                'crossOrigin': True,
	            },
	            map_options={
	                'maxZoom': 18,
	                'minZoom': 7,
	                'zoom': 11,
	                'center': [47.5, 13.6],
	                'doubleClickZoom': False,
	            },
	        ),
	    )

The attribute ``url_template`` specifies the URL template for the tile server. The attribute
``tile_layer_options`` allows to specify additional options for the tile layer. The attribute
``map_options`` allows to specify additional options for the map. Please refer to the Leaflet
documentation for details on the available options.

This ``GeoMapWidget`` has no control elements, so users can only view the map and cannot add any
markers, polylines or polygons. After form submission, the map's bounding box is passed to the
server and can be used for various purposes.

.. _Leaflet: https://leafletjs.com/
.. _OpenStreetMap: https://www.openstreetmap.org/
.. _basemap.at: https://basemap.at/


Global Settings
===============

If the ``GeoMapWidget`` is instantiated without specifying the ``url_template``,
``tile_layer_options`` or ``map_options`` attributes, it can be configured to use global settings
for the map. This allows to set the default values for these attributes in Django's ``settings.py``
module:

.. code-block:: python
	:caption: settings.py

	GEOMAP_WIDGET = {
	    'urlTemplate': 'https://maps.wien.gv.at/basemap/geolandbasemap/normal/google3857/{z}/{y}/{x}.png',
	    'tileLayerOptions': {
	        'attribution': '&copy; <a href="http://basemap.at">Basemap.at</a>',
	        'detectRetina': True,
	        'crossOrigin': True,
	    },
	    'mapOptions': {
	        'maxZoom': 18,
	        'minZoom': 7,
	        'zoom': 11,
	        'center': [47.5, 13.6],
	        'doubleClickZoom': False,
	    },
	}


Attribute Reference for ``GeoMapWidget``
========================================

The ``GeoMapWidget`` inherits from :class:`django.forms.widgets.Textarea` class and hence accepts
all of its attributes. In addition, it accepts these attributes:


.. rubric:: ``controls_topleft``, ``controls_topright``, ``controls_bottomleft``, ``controls_bottomright``

If set, each of these attributes must be a list of instances of a class inheriting from
:class:`formset.geomap.controls.ControlElement`. They are used to specify an editor for a geographic
data structure. Currently these editors are implemented:

* :class:`formset.geomap.controls.PointEditor`
* :class:`formset.geomap.controls.PolylineEditor`
* :class:`formset.geomap.controls.PolygonEditor`
* :class:`formset.geomap.controls.MultiPolygonEditor`

Each of these editors can be used to add, edit and remove the corresponding geographic data
structures. Editors can also be grouped together by putting them inside a list.


.. rubric:: Geometry Editor Attributes

If the same editor is used multiple times, the attribute ``identifier`` must specify a string
which is unique for all control elements. It is used as prefix in the ``id`` record inside the
GeoJSON data structure.

Each editor can accept an optional custom icon for the control button. The attribute is named
``add_button_icon``. If unset, a default icon is used. If a custom icon is specified, it must be a
string containing the path to an SVG file located in a templates folder.

Each editor can accept an optional custom icon for the delete button appearing in the popup.
The attribute is named ``delete_button_icon``. If unset, a default icon is used. If a custom icon
is specified, it must be be a string containing the path to an SVG file located in a templates
folder.


.. rubric:: :class:`formset.geomap.controls.PointEditor`

This editor looks for an optional custom marker symbol inside the Django template folders. The path
of this template is ``geomap/markers/{identifier}.json``, where ``{identifier}`` is the string
specified in the ``identifier`` attribute of the ``PointEditor``. If this template is not found, 
the default marker symbol is used. The marker must be specified through a dictionary containing the
following keys:

* ``iconUrl``: A string containing the path to an image file located in a static folder.
* ``iconSize``: A list of two integers specifying the width and height of the icon in pixels.
* ``iconAnchor``: A list of two integers specifying the point of the icon which will correspond to
  the marker's location. The coordinates are given in pixels relative to the top left corner of
  the icon image.
* ``popupAnchor``: A list of two integers specifying the point from which popups will "open",
  relative to the icon anchor. The coordinates are given in pixels relative to the top left corner
  of the icon image.


.. rubric:: Limit Number of Entities

Each editor can accept an optional minimum- and maximum number of entities to be added. They are
named ``min_markers`` and ``max_markers`` for the :class:`formset.geomap.controls.PointEditor`,
``min_polylines`` and ``max_polylines`` for the :class:`formset.geomap.controls.PolylineEditor`,
``min_polygons`` and ``max_polygons`` for the :class:`formset.geomap.controls.PolygonEditor` and
:class:`formset.geomap.controls.MultiPolygonEditor`. If unset no limit is enforced. If a minimum
number is specified, the user must add at least that many entities, otherwise the form is considered
as invalid. If a maximum number is specified, the user cannot add more than that many entities.


.. rubric:: Attach Custom Form Dialogs

Each editor can accept an optional list of form dialogs to be attached to each of its entities.
The attribute is named ``dialog_forms``. If unset, no extra form dialogs are attached to the given
editor. This list must contain instances of a class inheriting from
:class:`formset.geomap.dialogs.GeoMapDialogForm`.

Classes inheriting from :class:`formset.geomap.dialogs.GeoMapDialogForm` must specify a member
string named ``extension``. This string is used to identify the ``properties`` record in the GeoJSON
data structure and must be unique accross all form dialogs attached to the ``GeoMapWidget``.


Implementation Details
======================

The implementation of the ``GeoMapWidget`` is based on the Leaflet_ JavaScript library. This differs
from the GeoDjango implementation, which is based on OpenLayers_. The Leaflet library is smaller,
has no extra dependencies, is easier to use and `far more popular`_. No additional third party
plugins such as Leaflet.Draw or Leaflet-Geoman are required. 

.. _OpenLayers: https://openlayers.org/
.. _far more popular: https://npmtrends.com/leaflet-vs-ol
