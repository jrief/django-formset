.. _geographic-data:

==================================
Editing Geographic Data Structures
==================================

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

**django-formset** offers the special model field :class:`formset.modelfields.geomap.GeoMapField`,
the special form field :class:`formset.formfields.geomap.GeoMapField`, and the special widget
class :class:`formset.widgets.geomap.GeoMapWidget` to create a customized geographic editor
component. The widget can be configured to edit multiple geographic data structures at

.. _world-class geographic web framework: https://docs.djangoproject.com/en/stable/ref/contrib/gis/
.. _RFC-7946: https://datatracker.ietf.org/doc/html/rfc7946
.. _JSONField: https://docs.djangoproject.com/en/stable/ref/models/fields/#jsonfield
.. _PostGIS: https://postgis.net/
.. _SpatiaLite: https://www.gaia-gis.it/fossil/libspatialite/index
