.. _history:

=========================
History of django-formset
=========================

In 2012 I started to use AngularJS_ and was impressed by its simplicity. I really liked that it
became possible to use HTML as a declaration language without having to attach JavaScript modules
to elements inside a separate ``<script>`` tag. For me the `Angular form validation`_ library was
especially useful, because it allowed me to transfer the server-side field constraints to the
client, in order to perform a pre-validation without violating the DRY principle.

To get this working, I created the interface library django-angular_, which by 2015 gained quite
some popularity, because it allowed developers to build interactive forms with client-side
validation, but without having to implement one line of JavaScript code on the client. This library
owns ~1.2k stars on GitHub and is still downloaded more than 6000 times [#1]_ a month.

.. _AngularJS: https://docs.angularjs.org/
.. _Angular form validation: https://www.guru99.com/angularjs-validation.html#3
.. _django-angular: https://github.com/jrief/django-angular

In 2016 Google announced `Angular version 2`_ which is a completely different framework. It is
much more focused on client-side development, rather than offering reusable HTML directives as
AngularJS did. Furthermore, Google stopped developing AngularJS and on January 11th, 2022 it even
announced to `discontinue long term support`_ for it. This meant that I had to look for other
solutions.

.. _Angular version 2: https://angular.io/
.. _discontinue long term support: https://blog.angular.io/discontinued-long-term-support-for-angularjs-cc066b82e65a

In the meantime a bunch of very powerful JavaScript frameworks emerged. Their main focus however
is, helping developers to write *client-side* applications. For Django developers, this means to 
add an additional layer of abstraction, for instance the `Django Rest Framework`_, so that the
client can communicate with the Django application, using a kind of standardized protocol. In many
applications this meant to write forms for the client and some serializers on the server, leading
to un-DRY and hard maintainable code. On DjangoCon Europe 2022, David Guillot gave an `excellent
talk`_ about this topic.

.. _Django Rest Framework: https://www.django-rest-framework.org/
.. _excellent talk: https://www.youtube.com/watch?v=3GObi93tjZI

Therefore I wanted to reimplement the functionality from **django-angular**, but this time without
dependending on any JavaScript framework. Reason is that first, I do not want to impose any
preferred framework on Django developers, and secondly, knowing their typical half life cycle will
be in a similar situation as in 2016 with AngularJS.

I therefore decided to go with `web components`_ and `HTML templates`_ but without any JavaScript
framework. This presumably is more future proof and open to a much wider Django community.

.. _web components: https://developer.mozilla.org/en-US/docs/Web/API/Web_components
.. _HTML templates: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/template

.. rubric:: Footnotes

.. [#1] https://pypistats.org/packages/django-angular
