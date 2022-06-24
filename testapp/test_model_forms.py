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
    dropbox = input_field.find_next_sibling('figure', class_='dj-dropbox')
    drag_item = dropbox.find('div')
    assert drag_item.text == "Drag file here"
    template = input_field.parent.find_next_sibling('template', class_='dj-dropbox-items')
    img_element = template.find('img')
    assert img_element is not None
    assert img_element.attrs['src'] == '${thumbnail_url}'
    figcaption = template.find('figcaption')
    assert figcaption is not None
    description_lists = figcaption.find_all('dl')
    if framework is None:
        assert len(description_lists) == 3
        assert description_lists[0].find('dt').string == "Name:"
        assert description_lists[0].find('dd').string == "${name}"
        assert description_lists[1].find('dt').string == "Content-Type:"
        assert description_lists[1].find('dd').string == "${content_type}"
        assert description_lists[2].find('dt').string == "Size:"
        assert description_lists[2].find('dd').string == "${size}"
    else:
        assert len(description_lists) == 2
        assert description_lists[0].find('dt').string == "Name:"
        assert description_lists[0].find('dd').string == "${name}"
        assert description_lists[1].find('dt').string == "Content-Type (Size):"
        assert description_lists[1].find('dd').string == "${content_type} (${size})"


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
    opinions = OpinionModel.objects.order_by('?').values_list('id', flat=True)
    form_data = {
        'full_name': "John Doe",
        'avatar': '',  # Django test client doesn't support this
        'gender': 'male',
        'birth_date': '1981-12-28',
        'opinion': opinions[0],
        'opinions': opinions[10:15],
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
    assert person.opinion.id == form_data['opinion']
    assert person.opinions.filter(id__in=list(form_data['opinions'])).count() == 5
    assert person.opinions.exclude(id__in=list(form_data['opinions'])).count() == 0
    assert person.continent == 2

    form_data.update({
        'full_name': "Jane Doe",
        'gender': 'female',
        'birth_date': '1984-03-15',
        'opinion': opinions[100],
        'opinions': opinions[190:201],
        'continent': '1',
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
    assert person.opinion.id == form_data['opinion']
    assert person.opinions.filter(id__in=list(form_data['opinions'])).count() == 11
    assert person.opinions.exclude(id__in=list(form_data['opinions'])).count() == 0
    assert person.continent == 1

    request = RequestFactory().get('/default/person')
    response = update_view(request, pk=person.pk)
    assert response.status_code == 200
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    django_formset = soup.find('django-formset')
    assert django_formset is not None
    input_field = django_formset.find(id='id_full_name')
    assert input_field.attrs['value'] == "Jane Doe"
    select_option = django_formset.find(id='id_opinion').find('option', {'selected': True})
    assert select_option.attrs['value'] == str(form_data['opinion'])
    script_options = json.loads(django_formset.find(id='id_opinions_initial').contents[0])
    script_options = list(map(int, script_options))
    script_options.sort()
    form_options = list(form_data['opinions'])
    form_options.sort()
    assert script_options == form_options
    select_option = django_formset.find(id='id_continent').find('option', {'selected': True})
    assert select_option.attrs['value'] == '1'
