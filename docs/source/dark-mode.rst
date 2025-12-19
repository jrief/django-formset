.. _dark-mode:

========================
Dark Mode User Interface
========================

Dark mode is a user interface design style that uses a dimmed and dark color theme for elements. It
is considered "night-friendly" because it reduces screen glare. In low-light environments,
activating **dark mode** can help reduce eye strain from bright screens. This is why **dark mode**
has become a popular feature on many websites, allowing users to switch from the standard "light
theme" whenever they prefer.

**django-formset** added support for **dark mode** in version 1.6. There are two different
approaches for switching to dark mode. One is by using the browser's built-in dark mode feature.
This typically is a system-wide setting that can be activated in your operating system. The other
is by adding a special icon to the user interface of the website that allows switching between light
and dark mode.

For web developers there is a third option, in the DevTools of your Chrome browser, click the three
dots menu and select "Rendering", then activate the checkbox labeled "Enable auto dark mode". In
Firefox one can switch to dark mode by clicking on the moon icon when examining the styles of an
HTML element. Switching the color scheme using the DevTools of your browser is like changing it in
the settings of your operating system. Usually however, a website should provide a way to switch
between light and dark mode.

**django-formset** does not provide any helpers for switching between light and dark mode. This
feature is left to the developer of the website but usually is provided by the CSS framework used
for the website. For example, **Bootstrap 5** understands the special attribute ``data-bs-theme``
added to the ``<html>`` element of a page. This attribute can have the values ``auto``, ``light``,
or ``dark``. When set to ``auto``, the operating system's dark mode setting is respected. When set
to ``light`` or ``dark`` mode, that mode is enforced. This page for instance offers a button to
switch between auto, light and dark mode. It is located in the top right corner of the page.

Components provided by the **django-formset** library adapt themselves to the styling of the used
CSS framework. This means that when the website switches to dark mode, these components must also
switch to dark mode. This is achieved by using CSS variables that are set to different values
depending on the color scheme. For instance, in Bootstrap the color of the text is set to
``var(--bs-body-color)`` which is either a dark grey in light mode, or a light grey in dark mode.
Whenever a mode switch occurs, an event handler intercepts this and reevaluates the styles of the
given native HTML element and then applies them to the given web component implementing the widget.

In **django-formset**, dark mode settings provided by the operating system work out of the box and
without the need to change any JavaScript code or to add additional CSS rules to the website's CSS
files, provided the used CSS framework supports it. This is the case for **Bootstrap 5**. If a
manual dark mode switcher is desired, then the only thing to take care of is to ensure that either
the ``<html>``- or the ``<body>``-element contains an attribute containing the substring "theme".
Valid attributes for instance are ``data-theme`` (used by Sphinx), ``theme`` or ``data-bs-theme``
(used by Bootstrap). This attribute must contain the value of the actual theme, it is observed by
this library and whenever it changes, the styles of the web components are updated accordingly.
