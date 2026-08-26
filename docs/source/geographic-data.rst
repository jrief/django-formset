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
it can be used to edit multiple geographic data structures at once. In addition to that, we can
attach zero to many customized form dialogs to each of those geographic editor components, allowing
to add arbitrary information to each of them. This data then is exported as GeoJSON according to the
specification RFC-7946_. This allows to store the edited geographic information in a database using
a JSONField_. This allows developers to use a database without GIS extensions, such as PostGIS_ or
SpatiaLite_, and still be able to edit geographic data structures in a convenient way.

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
	from formset.geomap import controls 
	from formset.widgets.geomap import GeoMapWidget
	
	class SimplePointForm(Form):
	    map = GeoMapField(
	        label="Map",
	        widget=GeoMapWidget(
	            controls_topleft=[
	                controls.PointEditor(max_markers=3),
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
of the map canvas, the user can start dragging a marker to a position of his choice. The user can
remove this marker again, by clicking on the marker and select the trash symbol appearing inside the
popup.


Using Custom Marker Symbols
---------------------------

In this example we create a map to edit the position of churches.

.. django-view:: churches_map_form
	:view-function: GeoMapView.as_view(form_class=geographic_data.ChurchesMapForm, extra_context={'framework': 'bootstrap', 'pre_id': 'churches-map-result'}, form_kwargs={'auto_id': 'cf_id_%s'})

	from django.contrib.staticfiles.storage import staticfiles_storage
	from django.forms.forms import Form
	from django.forms.fields import IntegerField
	from formset.formfields.geomap import GeoMapField
	from formset.formfields.richtext import RichTextField
	from formset.geomap import controls, dialogs 
	from formset.widgets.geomap import GeoMapWidget
	
	church_marker = {
	    'iconUrl': staticfiles_storage.url('testapp/geomap-markers/church.svg'),
	    'iconSize': [32, 32],
	    'iconAnchor': [16, 35],
	    'popupAnchor': [0, -28],
	}

	class ChurchCapacityForm(dialogs.GeoMapDialogForm):
	    title = "Edit Capacity"
	    extension = 'capacity'
	    properties_map = {'max_visitors': 'max_visitors', 'description': 'description'}
	    icon = 'testapp/icons/users.svg'

	    max_visitors = IntegerField()
	    description = RichTextField(required=False)


	class ChurchesMapForm(Form):
	    map = GeoMapField(
	        label="Map of Churches",
	        widget=GeoMapWidget(
	            controls_topright=[
	                controls.PointEditor(
	                    identifier='church_editor',
	                    add_button_icon='testapp/icons/add-church-marker.svg',
	                    marker=church_marker,
	                    dialog_forms=[
	                        ChurchCapacityForm(),
	                    ],
	                ),
	            ],
	        ),
	    )

Here we replace the default marker symbol against an SVG file of our choice. This alternative marker
is loaded as static file. We also replace the control button with a custom SVG icon and move it into
the upper right corner of the map canvas. The user can add as many church markers as he wants.

The last attribute to our ``PointEditor`` control is the ``dialog_forms`` attribute. This allows to
attach one or more custom form dialogs to each of the markers. In this example we attach a single
form dialog, which allows to edit the maximum number of visitors for each church together with a
short description using richtext. When the user clicks on the church marker, the popup now contains
an extra button to open a dialog with our ``ChurchCapacityForm`` as declared above.

On submission, the content of the ``map`` field is exported as GeoJSON, where each marker contains
a record named ``properties`` with a sub record named ``capacity``. That sub record contains the
values of the fields ``max_visitors`` and ``description`` as entered by the user.


Using the Model Form Field
--------------------------

In this example we store the content of the edited map inside a model field in the database.

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

Since we want to configure the map editor, we need to configure the widget for our ``map`` field
when creating a form for this model:

.. django-view:: churches_model_form
	:caption: forms.py
	:hide-view:

	from django.forms.models import ModelForm
	from formset.geomap.controls import (
		PointEditor, PolylineEditor, PolygonEditor, MultiPolygonEditor
	)
	from formset.widgets.geomap import GeoMapWidget
	from testapp.models import ChurchModel

	class ChurchModelForm(ModelForm):
	    class Meta:
	        model = ChurchModel
	        fields = ['map']
	        widgets = {
	            'map': GeoMapWidget(
	                controls_bottomleft=[
	                    [PolylineEditor(), PolygonEditor(), MultiPolygonEditor()],
	                    PointEditor(),
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

Here we use four control elements, ``PointEditor``, ``PolylineEditor``, ``PolygonEditor`` and
``MultiPolygonEditor``. Users can add as many of them as they need. Users can also edit existing
markers by simple dragging them. The polylines and polygons can be edited by dragging their vertex
markers. Each vertex has a halfway marker, which allows to add a new vertex in between two existing
vertices. With a short click on a vertex marker, the adjacent vertices are merged. When clicking on
a marker, polyline or polygon, a popup appears with a trash button to remove that entity.

A multipolygon can be used to represent a polygon with holes. The outer polygon and the inner
polygons are represented as separate polygons inside the same data structure. In order to add a new
separate polygon to a multipolygon, a user must click on the polygon which opens the popup, and then
click on the "Add Polygon" button.

The ``GeoMapWidget`` can be configured to display the control buttons in any of the four corners of
the map canvas by using the attributes ``controls_topleft``, ``controls_topright``,
``controls_bottomleft`` and ``controls_bottomright``. Control buttons can be grouped together by
putting them inside a list.


Adopting the Map
----------------

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


Implementation Details
----------------------

The implementation of the ``GeoMapWidget`` is based on the Leaflet_ JavaScript library. This differs
from the GeoDjango implementation, which is based on OpenLayers_. The Leaflet has a more modern API
and is easier to use. No additional third party plugins are required. 

.. _OpenLayers: https://openlayers.org/
