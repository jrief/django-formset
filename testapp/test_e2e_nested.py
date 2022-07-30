import json
import pytest

from django.urls import path

from formset.utils import MARKED_FOR_REMOVAL
from formset.views import FormCollectionView

from .forms.nested import NestedCollection


nested_collection_level1 = NestedCollection.declared_holders['level1'].replicate()
nested_collection_level1.declared_holders['level2'].declared_holders['level3'].extra_siblings = 0


class NestedCollectionNoSiblings(NestedCollection):
    extra_siblings = 0

    level1 = nested_collection_level1


urlpatterns = [
    path('nested', FormCollectionView.as_view(
        collection_class=NestedCollection,
        template_name='testapp/form-collection.html',
        success_url='/success',
    ), name='nested'),
    path('nested_i', FormCollectionView.as_view(
        collection_class=NestedCollectionNoSiblings,
        template_name='testapp/form-collection.html',
        success_url='/success',
        initial=[{
            'campum': {'agro': 'aa'},
            'level1': {
                'campum': {'agro': 'bb'},
                'level2': {
                    'campum': {'agro': 'cc'},
                    'level3': [
                        {'campum': {'agro': 'dd'}},
                        {'campum': {'agro': 'ee'}},
                    ],
                },
            },
        }],
    ), name='nested_i'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['nested', 'nested_i'])
def test_nested_default(page, mocker):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 7
    page.fill('#id_0\\.campum\\.agro', "AA")
    page.fill('#id_0\\.level1\\.campum\\.agro', "BB")
    page.fill('#id_0\\.level1\\.level2\\.campum\\.agro', "CC")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.0\\.campum\\.agro', "DD")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro', "EE")
    page.query_selector('#id_0\\.campum\\.agro').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    response = json.loads(spy.call_args.args[1].body)
    assert response == {
        'formset_data': [{
            'level1': {
                'level2': {
                    'level3': [
                        {'campum': {'agro': 'DD'}},
                        {'campum': {'agro': 'EE'}},
                    ],
                    'campum': {'agro': 'CC'},
                },
                'campum': {'agro': 'BB'},
            },
            'campum': {'agro': 'AA'},
        }]
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['nested', 'nested_i'])
def test_nested_add_inner(page, mocker):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 7
    page.fill('#id_0\\.campum\\.agro', "AA")
    page.fill('#id_0\\.level1\\.campum\\.agro', "BB")
    page.fill('#id_0\\.level1\\.level2\\.campum\\.agro', "CC")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.0\\.campum\\.agro', "DD")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro', "EE")
    page.click('template[prefix="0.level1.level2.level3"] + button.add-collection')
    page.fill('#id_0\\.level1\\.level2\\.level3\\.2\\.campum\\.agro', "FF")
    page.query_selector('#id_0\\.campum\\.agro').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    response = json.loads(spy.call_args.args[1].body)
    assert response == {
        'formset_data': [{
            'level1': {
                'level2': {
                    'level3': [
                        {'campum': {'agro': 'DD'}},
                        {'campum': {'agro': 'EE'}},
                        {'campum': {'agro': 'FF'}},
                    ],
                    'campum': {'agro': 'CC'},
                },
                'campum': {'agro': 'BB'},
            },
            'campum': {'agro': 'AA'},
        }]
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['nested', 'nested_i'])
def test_nested_remove_inner_first(page, mocker, viewname):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 7
    page.fill('#id_0\\.campum\\.agro', "AA")
    page.fill('#id_0\\.level1\\.campum\\.agro', "BB")
    page.fill('#id_0\\.level1\\.level2\\.campum\\.agro', "CC")
    page.click('template[prefix="0.level1.level2.level3"] + button.add-collection')
    page.hover('#id_0\\.level1\\.level2\\.level3\\.0\\.campum')
    formset.wait_for_selector('#id_0\\.level1\\.level2\\.level3\\.0\\.campum + button.remove-collection').click()
    page.fill('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro', "DD")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.2\\.campum\\.agro', "EE")
    page.query_selector('#id_0\\.campum\\.agro').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    response = json.loads(spy.call_args.args[1].body)
    assert response == {
        'formset_data': [{
            'level1': {
                'level2': {
                    'level3': [
                        {'campum': {
                            'agro': '' if viewname == 'nested' else 'dd',
                            MARKED_FOR_REMOVAL: MARKED_FOR_REMOVAL
                        }},
                        {'campum': {'agro': 'DD'}},
                        {'campum': {'agro': 'EE'}},
                    ],
                    'campum': {'agro': 'CC'},
                },
                'campum': {'agro': 'BB'},
            },
            'campum': {'agro': 'AA'},
        }]
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['nested', 'nested_i'])
def test_nested_remove_inner_last(page, mocker):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 7
    page.fill('#id_0\\.campum\\.agro', "AA")
    page.fill('#id_0\\.level1\\.campum\\.agro', "BB")
    page.fill('#id_0\\.level1\\.level2\\.campum\\.agro', "CC")
    page.click('template[prefix="0.level1.level2.level3"] + button.add-collection')
    page.hover('#id_0\\.level1\\.level2\\.level3\\.2\\.campum')
    formset.wait_for_selector('#id_0\\.level1\\.level2\\.level3\\.2\\.campum + button.remove-collection').click()
    page.fill('#id_0\\.level1\\.level2\\.level3\\.0\\.campum\\.agro', "DD")
    page.fill('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro', "EE")
    page.query_selector('#id_0\\.campum\\.agro').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    response = json.loads(spy.call_args.args[1].body)
    assert response == {
        'formset_data': [{
            'level1': {
                'level2': {
                    'level3': [
                        {'campum': {'agro': 'DD'}},
                        {'campum': {'agro': 'EE'}},
                    ],
                    'campum': {'agro': 'CC'},
                },
                'campum': {'agro': 'BB'},
            },
            'campum': {'agro': 'AA'},
        }]
    }


@pytest.mark.skip(reason="not ready yet")
@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['nested', 'nested_i'])
def test_nested_reset(page, mocker, viewname):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 7
    spy = mocker.spy(FormCollectionView, 'post')
    if viewname == 'nested':
        expected = {
            'formset_data': [{
                'level1': {
                    'level2': {
                        'level3': [
                            {'campum': {'agro': ''}},
                            {'campum': {'agro': ''}},
                        ],
                        'campum': {'agro': ''},
                    },
                    'campum': {'agro': ''},
                },
                'campum': {'agro': ''},
            }]
        }
    else:
        expected = {
            'formset_data': [{
                'level1': {
                    'level2': {
                        'level3': [
                            {'campum': {'agro': 'dd'}},
                            {'campum': {'agro': 'ee'}},
                        ],
                        'campum': {'agro': 'cc'},
                    },
                    'campum': {'agro': 'bb'},
                },
                'campum': {'agro': 'aa'},
            }]
        }
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    assert json.loads(spy.call_args.args[1].body) == expected
    formset = page.query_selector('django-formset')

    page.fill('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro', "EE")
    formset.evaluate('elem => elem.reset()')
    input_value = page.query_selector('#id_0\\.level1\\.level2\\.level3\\.1\\.campum\\.agro').input_value()
    if viewname == 'nested':
        assert input_value == ''
    else:
        assert input_value == 'ee'

    page.hover('#id_0\\.level1\\.level2\\.level3\\.0\\.campum')
    page.wait_for_selector('#id_0\\.level1\\.level2\\.level3\\.0\\.campum + button\\.remove-collection').click()
    page.screenshot(path=f'{viewname}.png')
    elem = formset.locator('django-form-collection[sibling-position="0"] > django-form-collection:last-of-type > django-form-collection:last-of-type > django-form-collection[sibling-position="0"]')
    assert elem.get_attribute('class') == 'dj-marked-for-removal'
    formset.evaluate('elem => elem.reset()')
    assert elem.get_attribute('class') == ''

    assert len(formset.query_selector_all('django-form-collection')) == 7
