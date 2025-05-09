from bs4 import BeautifulSoup

import pytest


from django.forms import fields, forms
from django.forms.models import ModelChoiceField
from django.views.generic.edit import UpdateView

from formset.collection import FormCollection
from formset.formfields.collection import CollectionField
from formset.forms import ModelForm
from formset.views import FormViewMixin

from testapp.models.component import Component
from testapp.models.person import PersonModel


class SlideForm(forms.Form):
    title = fields.CharField()
    owner = ModelChoiceField(PersonModel.objects.all())


class SlidesCollection(FormCollection):
    min_siblings = 0
    extra_siblings = 1
    slide_form = SlideForm()
    legend = "Slides"
    add_label = "Add Slide"
    ignore_marked_for_removal = True


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
def edit_view():
    view_class = type('EditView', (FormViewMixin, UpdateView), {})
    return view_class.as_view(
        template_name='testapp/native-form.html',
        form_class=CarouselForm,
        queryset=Component.objects.filter(type='carousel'),
    )


@pytest.mark.django_db
def test_render_empty_carousel(rf, edit_view):
    component = Component.objects.create(type='carousel', created_by='test_carousel')
    request = rf.get('/')
    response = edit_view(request, pk=component.pk)
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
