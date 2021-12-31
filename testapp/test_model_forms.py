import json
import pytest
from bs4 import BeautifulSoup

from django.test import Client, RequestFactory
from django.utils.timezone import datetime
from django.views.generic.edit import CreateView, UpdateView

from formset.views import FormViewMixin

from .forms.person import ModelPersonForm
from .models import OpinionModel, PersonModel


@pytest.fixture(params=[None, 'bootstrap', 'bulma', 'foundation', 'tailwind', 'uikit'])
def framework(request):
    return request.param


@pytest.fixture
def create_view(framework):
    view_class = type('CreateView', (FormViewMixin, CreateView), {})
    return view_class.as_view(
        template_name='testapp/native-form.html',
        form_class=ModelPersonForm,
        extra_context={'framework': framework},
        success_url = '/success',
    )


@pytest.fixture
def native_soup(create_view):
    view_initkwargs = create_view.view_initkwargs
    framework = view_initkwargs['extra_context']['framework']
    url = f'/{framework}/person' if framework else '/default/person'
    request = RequestFactory().get(url)
    response = create_view(request)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup, framework


@pytest.mark.django_db
def test_render_file_field(native_soup):
    soup, framework = native_soup
    django_formset = soup.find('django-formset')
    assert django_formset is not None
    input_field = django_formset.find(id='id_avatar')
    assert input_field is not None
    dropbox = input_field.find_next_sibling('ul', class_='dj-dropbox')
    drag_item = dropbox.find('li')
    assert drag_item.text == "Drag file here"
    template = input_field.parent.find_next_sibling('template', class_='dj-dropbox-items')
    list_items = template.find_all('li')
    assert len(list_items) == 2
    assert list_items[0].img is not None
    assert list_items[0].img.attrs['src'] == '${thumbnail_url}'
    figures = list_items[1].find_all('figure')
    if framework is None:
        return
    assert len(figures) == 2
    assert figures[0].figcaption is not None
    assert figures[0].figcaption.string == "Name:"
    assert figures[0].p is not None
    assert figures[0].p.text is not "${name}"
    assert figures[1].figcaption is not None
    assert figures[1].figcaption.string == "Content-Type (Size):"
    assert figures[1].p is not None
    assert figures[1].p.text is not "${content_type} (${size})"


@pytest.mark.django_db
def test_render_radio_field(native_soup):
    soup, framework = native_soup
    django_formset = soup.find('django-formset')
    assert django_formset is not None
    div_element = django_formset.find(id='id_gender')
    input_fields = div_element.find_all('input', {'type': 'radio'})
    assert len(input_fields) == 2
    assert input_fields[0].attrs['id'] == 'id_gender_0'
    assert input_fields[0].attrs['name'] == 'gender'
    assert input_fields[0].attrs['value'] == 'female'
    assert input_fields[1].attrs['id'] == 'id_gender_1'
    assert input_fields[1].attrs['name'] == 'gender'
    assert input_fields[1].attrs['value'] == 'male'
    if framework == 'foundation':
        assert input_fields[0].next_sibling.attrs['for'] == 'id_gender_0'
        assert input_fields[1].next_sibling.attrs['for'] == 'id_gender_1'
        assert input_fields[0].next_sibling.text.strip() == "Female"
        assert input_fields[1].next_sibling.text.strip() == "Male"
    else:
        assert input_fields[0].parent.attrs['for'] == 'id_gender_0'
        assert input_fields[1].parent.attrs['for'] == 'id_gender_1'
        assert input_fields[0].parent.text.strip() == "Female"
        assert input_fields[1].parent.text.strip() == "Male"


@pytest.fixture(scope='function')
def uploaded_file(native_soup):
    client = Client()
    url = '/default/person'
    with open('testapp/assets/python-django.png', 'rb') as fp:
        response = client.post(url, {'temp_file': fp, 'image_height': 128})
    assert response.status_code == 200
    uploaded_data = response.json()
    assert uploaded_data['content_type'] == 'image/png'
    return uploaded_data


@pytest.fixture
def update_view():
    view_class = type('UpdateView', (FormViewMixin, UpdateView), {})
    return view_class.as_view(
        model=PersonModel,
        template_name='testapp/native-form.html',
        form_class=ModelPersonForm,
        success_url='/success',
    )


@pytest.mark.django_db
def test_modify_person(create_view, update_view):
    form_data = {
        'full_name': "John Doe",
        'avatar': '',  # Django test client doesn't support this
        'gender': 'male',
        'birth_date': '1981-12-28',
        'opinion': '1',
        'continent': '2',
    }
    request = RequestFactory().post('/default/person', form_data)
    response = create_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    person = PersonModel.objects.last()
    assert person is not None
    assert person.full_name == "John Doe"
    assert person.gender == 'male'
    assert person.birth_date == datetime(1981, 12, 28).date()
    assert person.opinion == OpinionModel.objects.get(pk=1)
    assert person.continent == 2

    form_data.update({
        'full_name': "Jane Doe",
        'gender': 'female',
        'birth_date': '1984-03-15',
    })
    request = RequestFactory().post('/default/person', form_data)
    response = update_view(request, pk=person.pk)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    person = PersonModel.objects.last()
    assert person is not None
    assert person.full_name == "Jane Doe"
    assert person.gender == 'female'
    assert person.birth_date == datetime(1984, 3, 15).date()
    assert person.opinion == OpinionModel.objects.get(pk=1)
    assert person.continent == 2

    request = RequestFactory().get('/default/person')
    response = update_view(request, pk=person.pk)
    assert response.status_code == 200
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    django_formset = soup.find('django-formset')
    assert django_formset is not None
    input_field = django_formset.find(id='id_full_name')
    assert input_field.attrs['value'] == "Jane Doe"
    select_option = django_formset.find(id='id_continent').find('option', {'selected': True})
    assert select_option.attrs['value'] == '2'
