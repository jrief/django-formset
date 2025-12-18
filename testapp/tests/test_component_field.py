from bs4 import BeautifulSoup

import json
import pytest


from django.forms import fields, forms
from django.forms.models import ModelChoiceField
from django.views.generic.edit import UpdateView

from formset.collection import AddSiblingActivator, FormCollection
from formset.formfields.collection import CollectionField
from formset.forms import ModelForm
from formset.views import FormViewMixin

from testapp.models.component import Component
from testapp.models.reporter import Reporter


class SlideForm(forms.Form):
    title = fields.CharField()
    reporter = ModelChoiceField(Reporter.objects.all())


class SlidesCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    slide_form = SlideForm()
    legend = "Slides"
    induce_add_sibling = '.add_slide:active'
    ignore_marked_for_removal = True

    add_slide = AddSiblingActivator("Add Slide")


class CarouselForm(ModelForm):
    interval = fields.IntegerField()
    slides = CollectionField(SlidesCollection)

    class Meta:
        model = Component
        fields = ['context']
        fields_map = {
            'context': ['interval', 'slides'],
        }


@pytest.fixture
def view_class():
    return type('EditView', (FormViewMixin, UpdateView), {
        'template_name': 'testapp/native-form.html',
        'model': Component,
        'success_url': '/success/',
    })


@pytest.mark.django_db
def test_render_empty_carousel(rf, view_class):
    component = Component.objects.create(type='carousel', created_by='test_carousel')
    request = rf.get('/')
    response = view_class.as_view(
        form_class=CarouselForm,
        queryset=Component.objects.filter(type='carousel'),
    )(request, pk=component.pk)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset = soup.find('django-formset')
    form = formset.find(role='form')
    input_fields = form.find_all('input')
    assert len(input_fields) == 3
    expected = soup.new_tag(
        name='input',
        attrs={'type': 'number', 'name': 'interval', 'id': 'id_interval', 'form': 'id_carouselform', 'required': ''},
    )
    assert input_fields[0] == expected
    expected = soup.new_tag(
        name='input',
        attrs={'type': 'text', 'name': 'title', 'id': 'id_slides.0.slide_form.title', 'form': 'id_slides.0.slide_form', 'required': ''},
    )
    assert input_fields[1] == expected
    expected['id'] = 'id_slides.${siblingId}.slide_form.title'
    expected['form'] = 'id_slides.${siblingId}.slide_form'
    assert input_fields[2] == expected
    select_fields = form.find_all('select')
    assert len(select_fields) == 2
    assert select_fields[0]['id'] == 'id_slides.0.slide_form.reporter'
    assert 'value' not in select_fields[0]
    assert select_fields[1]['id'] == 'id_slides.${siblingId}.slide_form.reporter'


@pytest.mark.django_db
def test_render_prefilled_carousel(rf, view_class):
    reporter = Reporter.objects.order_by('?').first()
    component = Component.objects.create(
        type='carousel',
        created_by='test_carousel',
        context={'interval': 5000, 'slides': [
            {'slide_form': {'title': 'Slide 1', 'reporter': {'model': 'testapp.reporter', 'pk': reporter.pk}}},
            {'slide_form': {'title': 'Slide 2', 'reporter': {'model': 'testapp.reporter', 'pk': reporter.pk}}},
        ]},
    )
    request = rf.get('/')
    response = view_class.as_view(
        form_class=CarouselForm,
        queryset=Component.objects.filter(type='carousel'),
    )(request, pk=component.pk)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset = soup.find('django-formset')
    form = formset.find(role='form')
    input_fields = form.find_all('input')
    assert len(input_fields) == 5
    expected = soup.new_tag(
        name='input',
        attrs={'type': 'number', 'name': 'interval', 'id': 'id_interval', 'form': 'id_carouselform', 'required': '', 'value': '5000'},
    )
    assert input_fields[0] == expected
    expected = soup.new_tag(
        name='input',
        attrs={'type': 'text', 'name': 'title', 'id': 'id_slides.0.slide_form.title', 'form': 'id_slides.0.slide_form', 'required': '', 'value': "Slide 1"},
    )
    assert input_fields[1] == expected
    expected['form'] = 'id_slides.1.slide_form'
    expected['id'] = 'id_slides.1.slide_form.title'
    expected['value'] = "Slide 2"
    assert input_fields[2] == expected
    expected['form'] = 'id_slides.2.slide_form'
    expected['id'] = 'id_slides.2.slide_form.title'
    del expected['value']
    assert input_fields[3] == expected
    expected['id'] = 'id_slides.${siblingId}.slide_form.title'
    expected['form'] = 'id_slides.${siblingId}.slide_form'
    assert input_fields[4] == expected
    select_fields = form.find_all('select')
    assert len(select_fields) == 4
    selected_option = select_fields[0].find('option', selected=True)
    assert selected_option['value'] == str(reporter.pk)


@pytest.mark.django_db
def test_edit_carousel_invalid(rf, view_class):
    component = Component.objects.create(
        type='carousel',
        created_by='test_carousel',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'interval': 'XYZ',
            'slides': [
                {'slide_form': {'title': 'Slide A', 'reporter': 'invalid_data'}},
                {'slide_form': {'title': 'Slide B'}},
            ],
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=CarouselForm,
        queryset=Component.objects.filter(type='carousel'),
    )(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'interval': ["Enter a whole number."],
        'slides': [
            {'slide_form': {'reporter': ["Select a valid choice. That choice is not one of the available choices."]}},
            {'slide_form': {'reporter': ["This field is required."]}},
        ],
    }
    assert json.loads(response.getvalue()) == expected


@pytest.mark.django_db
def test_edit_carousel_valid(rf, view_class):
    reporter1 = Reporter.objects.order_by('?').first()
    reporter2 = Reporter.objects.order_by('?').first()
    component = Component.objects.create(
        type='carousel',
        created_by='test_carousel',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'interval': 3000,
            'slides': [
                {'slide_form': {'title': 'Slide A', 'reporter': reporter1.pk}},
                {'slide_form': {'title': 'Slide B', 'reporter': reporter2.pk}},
            ],
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=CarouselForm,
        queryset=Component.objects.filter(type='carousel'),
    )(request, pk=component.pk)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success/'
    component.refresh_from_db()
    expected = {
        'interval': 3000,
        'slides': [{
            'slide_form': {
                'title': "Slide A",
                'reporter': {'model': 'testapp.reporter', 'pk': reporter1.pk},
            },
        }, {
            'slide_form': {
                'title': "Slide B",
                'reporter': {'model': 'testapp.reporter', 'pk': reporter2.pk},
            },
        }],
    }
    assert component.context == expected


class AccordionItem(forms.Form):
    heading = fields.RegexField(r'^[A-Z][a-zA-Z0-9 ]+$')


class AccordionCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 0
    accordion_item = AccordionItem()
    legend = "Accordion"
    induce_add_sibling = '.add_item:active'
    ignore_marked_for_removal = True

    add_item = AddSiblingActivator("Add Accordion Item")


class AccordionForm(ModelForm):
    context = CollectionField(AccordionCollection)

    class Meta:
        model = Component
        fields = ['context']


@pytest.mark.django_db
def test_render_prefilled_accordion(rf, view_class):
    component = Component.objects.create(
        type='accordion',
        created_by='test_accordion',
        context=[
            {'accordion_item': {'heading': "Accordion 1"}},
            {'accordion_item': {'heading': "Accordion 2"}},
        ],
    )
    request = rf.get('/')
    response = view_class.as_view(
        form_class=AccordionForm,
        queryset=Component.objects.filter(type='accordion'),
    )(request, pk=component.pk)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset = soup.find('django-formset')
    form = formset.find(role='form')
    input_fields = form.find_all('input')
    assert len(input_fields) == 3
    attrs = {'type': 'text', 'name': 'heading', 'required': '', 'pattern': '^[A-Z][a-zA-Z0-9 ]+$'}
    expected = soup.new_tag(
        name='input',
        attrs=dict(attrs, id='id_context.0.accordion_item.heading', form='id_context.0.accordion_item', value="Accordion 1"),
    )
    assert input_fields[0] == expected
    expected = soup.new_tag(
        name='input',
        attrs=dict(attrs, id='id_context.1.accordion_item.heading', form='id_context.1.accordion_item', value="Accordion 2"),
    )
    assert input_fields[1] == expected
    expected = soup.new_tag(
        name='input',
        attrs=dict(attrs, id='id_context.${siblingId}.accordion_item.heading', form='id_context.${siblingId}.accordion_item'),
    )
    assert input_fields[2] == expected


@pytest.mark.django_db
def test_edit_accordion_invalid(rf, view_class):
    component = Component.objects.create(
        type='accordion',
        created_by='test_accordion',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'context': [
                {'accordion_item': {'heading': "accordion A"}},
                {'accordion_item': {}},
            ],
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=AccordionForm,
        queryset=Component.objects.filter(type='accordion'),
    )(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'context': [
            {'accordion_item': {'heading': ["Enter a valid value."]}},
            {'accordion_item': {'heading': ["This field is required."]}},
        ],
    }
    assert json.loads(response.getvalue()) == expected


@pytest.mark.django_db
def test_edit_accordion_valid(rf, view_class):
    component = Component.objects.create(
        type='accordion',
        created_by='test_accordion',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'context': [
                {'accordion_item': {'heading': "Accordion A"}},
                {'accordion_item': {'heading': "Accordion B"}},
            ],
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=AccordionForm,
        queryset=Component.objects.filter(type='accordion'),
    )(request, pk=component.pk)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success/'
    component.refresh_from_db()
    expected = [
        {'accordion_item': {'heading': "Accordion A"}},
        {'accordion_item': {'heading': "Accordion B"}},
    ]
    assert component.context == expected


class Jumbotron(forms.Form):
    heading = fields.RegexField(r'^[A-Z][a-zA-Z0-9 ]+$')


class JumbotronCollection(FormCollection):
    item = Jumbotron()


class JumbotronForm(ModelForm):
    context = CollectionField(JumbotronCollection)

    class Meta:
        model = Component
        fields = ['context']


@pytest.mark.django_db
def test_render_prefilled_jumbotron(rf, view_class):
    component = Component.objects.create(
        type='jumbotron',
        created_by='test_jumbotron',
        context={'item': {'heading': "Jumbotron"}},
    )
    request = rf.get('/')
    response = view_class.as_view(
        form_class=JumbotronForm,
        queryset=Component.objects.filter(type='jumbotron'),
    )(request, pk=component.pk)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset = soup.find('django-formset')
    form = formset.find(role='form')
    input_fields = form.find_all('input')
    assert len(input_fields) == 1
    attrs = {'type': 'text', 'name': 'heading', 'required': '', 'pattern': '^[A-Z][a-zA-Z0-9 ]+$'}
    expected = soup.new_tag(
        name='input',
        attrs=dict(attrs, id='id_context.item.heading', form='id_context.item', value="Jumbotron"),
    )
    assert input_fields[0] == expected


@pytest.mark.django_db
def test_edit_jumbotron_invalid(rf, view_class):
    component = Component.objects.create(
        type='jumbotron',
        created_by='test_jumbotron',
    )
    assert component.context == {}
    view_func = view_class.as_view(
        form_class=JumbotronForm,
        queryset=Component.objects.filter(type='jumbotron'),
    )
    form_data = {
        'formset_data': {
            'context': {'item': {'heading': "jumbotron"}},
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'context': {'item': {'heading': ["Enter a valid value."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data']['context']['item'].pop('heading')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'context': {'item': {'heading': ["This field is required."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data']['context'].pop('item')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'context': {'item': {'__all__': ["Form data is missing."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data'].pop('context')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    assert json.loads(response.getvalue()) == expected


@pytest.mark.django_db
def test_edit_jumbotron_valid(rf, view_class):
    component = Component.objects.create(
        type='jumbotron',
        created_by='test_jumbotron',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'context': {'item': {'heading': "Jumbotron"}},
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=JumbotronForm,
        queryset=Component.objects.filter(type='jumbotron'),
    )(request, pk=component.pk)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success/'
    component.refresh_from_db()
    assert component.context == {'item': {'heading': "Jumbotron"}}


class JumbomapForm(JumbotronForm):
    jumbotron = CollectionField(JumbotronCollection)

    class Meta:
        model = Component
        fields = ['context']
        fields_map = {'context': ['jumbotron']}


@pytest.mark.django_db
def test_render_prefilled_jumbomap(rf, view_class):
    component = Component.objects.create(
        type='jumbomap',
        created_by='test_jumbomap',
        context={'jumbotron': {'item': {'heading': "Jumbomap"}}},
    )
    request = rf.get('/')
    response = view_class.as_view(
        form_class=JumbomapForm,
        queryset=Component.objects.filter(type='jumbomap'),
    )(request, pk=component.pk)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset = soup.find('django-formset')
    form = formset.find(role='form')
    input_fields = form.find_all('input')
    assert len(input_fields) == 1
    attrs = {'type': 'text', 'name': 'heading', 'required': '', 'pattern': '^[A-Z][a-zA-Z0-9 ]+$'}
    expected = soup.new_tag(
        name='input',
        attrs=dict(attrs, id='id_jumbotron.item.heading', form='id_jumbotron.item', value="Jumbomap"),
    )
    assert input_fields[0] == expected


@pytest.mark.django_db
def test_edit_jumbomap_invalid(rf, view_class):
    component = Component.objects.create(
        type='jumbomap',
        created_by='test_jumbomap',
    )
    assert component.context == {}
    view_func = view_class.as_view(
        form_class=JumbomapForm,
        queryset=Component.objects.filter(type='jumbomap'),
    )
    form_data = {
        'formset_data': {
            'jumbotron': {'item': {'heading': "jumbotron"}},
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'jumbotron': {'item': {'heading': ["Enter a valid value."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data']['jumbotron']['item'].pop('heading')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'jumbotron': {'item': {'heading': ["This field is required."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data']['jumbotron'].pop('item')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    expected = {
        'jumbotron': {'item': {'__all__': ["Form data is missing."]}},
    }
    assert json.loads(response.getvalue()) == expected

    form_data['formset_data'].pop('jumbotron')
    request = rf.post('/', form_data, content_type='application/json')
    response = view_func(request, pk=component.pk)
    assert response.status_code == 422
    assert json.loads(response.getvalue()) == expected


@pytest.mark.django_db
def test_edit_jumbomap_valid(rf, view_class):
    component = Component.objects.create(
        type='jumbomap',
        created_by='test_jumbomap',
    )
    assert component.context == {}
    form_data = {
        'formset_data': {
            'jumbotron': {'item': {'heading': "Jumbotron"}},
        }
    }
    request = rf.post('/', form_data, content_type='application/json')
    response = view_class.as_view(
        form_class=JumbomapForm,
        queryset=Component.objects.filter(type='jumbomap'),
    )(request, pk=component.pk)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success/'
    component.refresh_from_db()
    assert component.context == {'jumbotron': {'item': {'heading': "Jumbotron"}}}
