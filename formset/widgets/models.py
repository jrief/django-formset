from functools import reduce
from inspect import isclass
from operator import and_, or_

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db.models.query_utils import Q
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.forms.widgets import Select, SelectMultiple, Widget
from django.utils.encoding import uri_to_iri
from django.utils.translation import gettext_lazy as _


class SimpleModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for obj in queryset:
            yield self.choice(obj)

    def __len__(self):
        return self.queryset.count()

    def __bool__(self):
        return self.queryset.exists()


class GroupedModelChoiceIterator(SimpleModelChoiceIterator):
    group_field_name = None

    def choice(self, obj):
        return (
            ModelChoiceIteratorValue(self.field.prepare_value(obj), obj),
            self.field.label_from_instance(obj),
            getattr(obj, self.group_field_name),
        )


class IncompleteSelectMixin:
    """
    Extra interfaces for widgets not loading the complete set of choices.
    """

    choices = ()
    max_prefetch_choices = 250
    search_lookup = None
    group_field_name = None
    filter_by = None
    use_filter_set = None

    def __init__(self, attrs=None, choices=(), search_lookup=None, group_field_name=None, filter_by=None, use_filter_set=None):
        if search_lookup:
            self.search_lookup = search_lookup
        if isinstance(self.search_lookup, str):
            self.search_lookup = [self.search_lookup]
        if isinstance(group_field_name, str):
            self.group_field_name = group_field_name
        if filter_by and use_filter_set:
            raise ImproperlyConfigured("Attributes 'filter_by' and 'use_filter_set' are mutually exclusive.")
        if isinstance(filter_by, dict):
            self.filter_by = filter_by
        elif (
            isclass(use_filter_set) and  # this avoids the need to import `django_filters.FilterSet`
            any((b.__module__, b.__name__) == ('django_filters.filterset', 'FilterSet') for b in use_filter_set.mro())
        ):
            self.use_filter_set = use_filter_set
        super().__init__(attrs, choices)

    def build_filter_query(self, filtervalues):
        queries = []
        for fieldname, lookup in self.filter_by.items():
            filtervalue = filtervalues[fieldname]
            if isinstance(filtervalue, list):
                subqueries = [Q(**{lookup: val if val else None}) for val in filtervalue]
                queries.append(reduce(or_, subqueries, Q()))
            elif isinstance(filtervalue, str):
                queries.append(Q(**{lookup: filtervalue}))
        try:
            return reduce(and_, queries, Q())
        except TypeError:
            raise ImproperlyConfigured(f"Invalid attribute 'filter_by' in {self.__class__}.")

    def build_search_query(self, search_term):
        search_term = uri_to_iri(search_term)
        try:
            return reduce(or_, (Q(**{sl: search_term}) for sl in self.search_lookup))
        except TypeError:
            raise ImproperlyConfigured(f"Invalid attribute 'search_lookup' in {self.__class__}.")

    def format_value(self, value):
        if value is None:
            return []
        if not isinstance(value, (tuple, list)):
            value = [value]
        return [str(v) if v is not None else "" for v in value]

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if isinstance(self.choices, SimpleModelChoiceIterator):
            if self.choices.queryset.count() > self.max_prefetch_choices:
                attrs['incomplete'] = True
            if self.filter_by:
                attrs['filter-by'] = ','.join(self.filter_by.keys())
            elif self.use_filter_set:
                attrs['filter-by'] = ','.join(self.use_filter_set.base_filters.keys())
        return attrs

    def get_context(self, name, value, attrs):
        if isinstance(self.choices, ModelChoiceIterator):
            if self.group_field_name:
                self.optgroups = self._optgroups_model_choice
                self.choices.queryset = self.choices.queryset.order_by(self.group_field_name)
                self.choices.group_field_name = self.group_field_name
                self.choices.__class__ = GroupedModelChoiceIterator
            else:
                self.optgroups = self._options_model_choice
                self.choices.__class__ = SimpleModelChoiceIterator
        else:
            self.optgroups = self._optgroups_static_choice
        context = super().get_context(name, value, attrs)
        return context

    def _optgroups_static_choice(self, name, values, attrs=None):
        optgroups = super().optgroups(name, values, attrs)
        return optgroups

    def _options_model_choice(self, name, values, attrs=None):
        values_list = [str(val) for val in values]
        optgroups, counter = [], 0
        for val, label in self.choices:
            if counter == self.max_prefetch_choices:
                break
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if selected := val in values_list:
                values_list.remove(val)
            optgroups.append((None, [{'value': val, 'label': label, 'selected': selected}], counter))
            counter += 1
        for val in values_list:
            try:
                obj = self.choices.queryset.get(pk=val)
            except ObjectDoesNotExist:
                continue
            label = self.choices.field.label_from_instance(obj)
            optgroups.append((None, [{'value': str(val), 'label': label, 'selected': True}], counter))
            counter += 1
        return optgroups

    def _optgroups_model_choice(self, name, values, attrs=None):
        values_list = [str(val) for val in values]
        optgroups, prev_group_name, counter = [], '-', 0

        # first handle selected values
        for counter, val in enumerate(values_list, counter):
            try:
                obj = self.choices.queryset.get(pk=val)
            except ObjectDoesNotExist:
                continue
            label = self.choices.field.label_from_instance(obj)
            group_name = getattr(obj, self.group_field_name) if self.group_field_name else None
            optgroup = list(filter(lambda item: item[0] == group_name, optgroups))
            if optgroup:
                optgroup[-1][1].append({'value': str(val), 'label': label, 'selected': True})
            else:
                subgroup = [{'value': str(val), 'label': label, 'selected': True}]
                optgroups.append((group_name, subgroup, counter))

        # afterwards handle the remaining values
        for counter, (val, label, group_name) in enumerate(self.choices, counter):
            if counter == self.max_prefetch_choices:
                break
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if prev_group_name != group_name:
                prev_group_name = group_name
                subgroup = [{'value': val, 'label': label}]
                optgroups.append((group_name, subgroup, counter))
            else:
                subgroup.append({'value': val, 'label': label})
        return optgroups


class Selectize(IncompleteSelectMixin, Select):
    """
    Render widget suitable for TomSelect
    """
    template_name = 'formset/default/widgets/selectize.html'
    webcomponent = 'django-selectize'
    placeholder = _("Select")

    def __init__(
        self,
        attrs=None,
        choices=(),
        search_lookup=None,
        group_field_name=None,
        filter_by=None,
        use_filter_set=None,
        placeholder=None,
    ):
        super().__init__(attrs, choices, search_lookup, group_field_name, filter_by, use_filter_set)
        if placeholder is not None:
            self.placeholder = placeholder

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['is'] = self.webcomponent
        if self.is_required:
            attrs['required'] = True  # Selectize overrides the default behaviour
        return attrs

    def _optgroups_static_choice(self, name, values, attrs=None):
        options = [(None, [{'value': '', 'label': self.placeholder}], None)]
        options.extend(super()._optgroups_static_choice(name, values, attrs))
        return options

    def _options_model_choice(self, name, values, attrs=None):
        options = [(None, [{'value': '', 'label': self.placeholder}], None)]
        options.extend(super()._options_model_choice(name, values, attrs))
        return options

    def _optgroups_model_choice(self, name, values, attrs=None):
        optgroups = [(None, [{'value': '', 'label': self.placeholder}], None)]
        optgroups.extend(super()._optgroups_model_choice(name, values, attrs))
        return optgroups


class CountrySelectize(Selectize):
    template_name = 'formset/default/widgets/selectize_country.html'
    webcomponent = 'django-selectize-country'


class SelectizeMultiple(Selectize):
    allow_multiple_selected = True
    max_items = 5

    def __init__(self, max_items=None, **kwargs):
        super().__init__(**kwargs)
        if max_items:
            self.max_items = max_items

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['max_items'] = self.max_items
        return attrs


class CountrySelectizeMultiple(SelectizeMultiple):
    template_name = 'formset/default/widgets/selectize_country.html'
    webcomponent = 'django-selectize-country'


class DualSelector(IncompleteSelectMixin, SelectMultiple):
    """
    Render widget suitable for the <select is="django-dual-selector"> widget
    """
    template_name = 'formset/default/widgets/dual_selector.html'


class DualSortableSelector(DualSelector):
    """
    Render widget suitable for the <select is="django-dual-sortable-selector"> widget
    """
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['is_sortable'] = True
        return context

    def _options_model_choice(self, name, values, attrs=None):
        values_list = [str(val) for val in values]
        optgroups, counter = [], 0
        # first create options from values_list, otherwise order is lost
        for val in values_list:
            try:
                obj = self.choices.queryset.get(pk=val)
            except ObjectDoesNotExist:
                continue
            label = self.choices.field.label_from_instance(obj)
            optgroups.append((None, [{'value': str(val), 'label': label, 'selected': True}], counter))
            counter += 1
        # then add remaining options up to max_prefetch_choices
        for val, label in self.choices:
            if counter >= self.max_prefetch_choices:
                break
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if val in values_list:
                continue
            optgroups.append((None, [{'value': val, 'label': label, 'selected': False}], counter))
            counter += 1
        return optgroups


class EmptyWidget(Widget):
    """
    Just a placeholder for a widget that does not render anything. Used by ShadowField.
    """

    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ""
