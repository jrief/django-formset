import pytest
import json

from django.forms import Field, Form, models
from django.urls import path

from formset.views import FormView
from formset.widgets import DualSelector

from testapp.models import OpinionModel


class NativeFormView(FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        for counter in range(1, 1000):
            label = f"Opinion {counter:04}"
            OpinionModel.objects.update_or_create(tenant=1, label=label)


def get_initial_opinion():
    return OpinionModel.objects.filter(tenant=1)[8]


def get_initial_opinions():
    return list(OpinionModel.objects.filter(tenant=1).values_list('id', flat=True)[41:55])


test_fields = dict(
    selector=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
        required=False,
    ),
    selector_complete=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1)[:100],
        widget=DualSelector(search_lookup='label__icontains'),
    ),
    selector_required=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
    ),
    selector_initialized=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
        initial=get_initial_opinions,
    ),
)

views = {
    f'selector{counter}': NativeFormView.as_view(
        form_class=type(f'{name}_form', (Form,), {'name': name, 'model_choice': field}),
    )
    for counter, (name, field) in enumerate(test_fields.items())
}

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.fixture
def view(viewname):
    return views[viewname]


@pytest.fixture
def form(view):
    return view.view_initkwargs['form_class']()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_form_validated(page, form):
    assert page.query_selector('django-formset form') is not None
    if form.name in ['selector', 'selector_initialized']:
        assert page.query_selector('django-formset form:valid') is not None
        assert page.query_selector('django-formset form:invalid') is None
    else:
        assert page.query_selector('django-formset form:valid') is None
        assert page.query_selector('django-formset form:invalid') is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_initial_value(page, form):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    value = selector_element.evaluate('elem => elem.getValue()')
    if form.name == 'selector_initialized':
        assert set(value) == set(str(k) for k in get_initial_opinions())
    else:
        assert value == []


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_move_all_right(page, mocker, form):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    incomplete = selector_element.get_attribute('incomplete') is not None
    selector_options = selector_element.query_selector_all('option')
    if form.name == 'selector_complete':
        assert incomplete is False
        assert len(selector_options) == 50
    else:
        assert incomplete is True
        assert len(selector_options) == DualSelector.max_prefetch_choices
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-all-right')
    assert button is not None
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    assert len(select_left_element.query_selector_all('option')) + len(select_right_element.query_selector_all('option')) == len(selector_options)
    if form.name == 'selector_initialized':
        assert len(select_right_element.query_selector_all('option')) == len(get_initial_opinions())
    else:
        assert len(select_right_element.query_selector_all('option')) == 0
    spy = mocker.spy(FormView, 'get')
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    while incomplete:
        left_option_values = set(o.get_attribute('value') for o in select_left_element.query_selector_all('option'))
        button.click()  # this triggers loading of more options
        right_option_values = right_option_values.union(left_option_values)
        assert right_option_values == set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
        assert spy.called is True
        assert spy.spy_return.status_code == 200
        content = json.loads(spy.spy_return.content)
        spy.reset_mock()
        assert len(select_left_element.query_selector_all('option')) == content['count']
        incomplete = content['incomplete']
        assert content['total_count'] == OpinionModel.objects.filter(tenant=1).count()
        if incomplete:
            assert len(selector_element.query_selector_all('option')) < content['total_count']
        else:
            assert len(selector_element.query_selector_all('option')) == content['total_count']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_move_selected_right(page, mocker, form):
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = set()
    for option in select_left_element.query_selector_all('option')[30:39]:
        left_option_values.add(option.get_attribute('value'))
        option.click(modifiers=['Shift'])
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    if form.name == 'selector_initialized':
        assert len(select_right_element.query_selector_all('option')) == len(get_initial_opinions())
        left_option_values.update(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    else:
        assert len(select_right_element.query_selector_all('option')) == 0
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-right')
    assert button is not None
    button.click()
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    assert left_option_values == right_option_values
    option = select_right_element.query_selector_all('option')[5]
    option.click()
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-left')
    assert button is not None
    button.click()
    left_option_values = set(o.get_attribute('value') for o in select_left_element.query_selector_all('option'))
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    assert option.get_attribute('value') in left_option_values
    assert option.get_attribute('value') not in right_option_values
    spy = mocker.spy(FormView, 'post')
    page.wait_for_selector('django-formset > p button').click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert set(request['formset_data']['model_choice']) == right_option_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_infinite_scroll(page, mocker, form):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    assert len(left_option_values) == DualSelector.max_prefetch_choices
    select_left_element.focus()
    spy = mocker.spy(FormView, 'get')
    select_left_element.select_option(left_option_values[DualSelector.max_prefetch_choices - 2])
    assert spy.called is False
    assert len(select_left_element.query_selector_all('option')) == DualSelector.max_prefetch_choices
    page.keyboard.press('ArrowDown')
    assert spy.called is True
    field_name = selector_element.get_attribute('name')
    params = spy.call_args.args[1].GET
    assert params['field'] == f'__default__.{field_name}'
    assert int(params['offset']) == DualSelector.max_prefetch_choices
    assert len(select_left_element.query_selector_all('option')) == 2 * DualSelector.max_prefetch_choices
    response = json.loads(spy.spy_return.content)
    assert response['count'] == DualSelector.max_prefetch_choices
    assert response['incomplete'] is True
    assert isinstance(response['items'], list)
    assert len(response['items']) == response['count']
