import pytest

from django.urls import path

from formset.views import FormView

from .forms.advertisement import AdvertisementForm


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class=AdvertisementForm
    success_url = '/success'


urlpatterns = [
    path('new_advertisement', DemoFormView.as_view(), name='new_advertisement'),
    path('current_advertisement', DemoFormView.as_view(initial={'slug': "foo-bar"}), name='current_advertisement'),
]


@pytest.fixture
def richtext_wrapper(page):
    return page.locator('.dj-richtext-wrapper')


@pytest.fixture
def menubar(richtext_wrapper):
    menubar = richtext_wrapper.locator('[role="menubar"]')
    menubar.element_handle() is not None
    return menubar


@pytest.fixture
def contenteditable(richtext_wrapper):
    contenteditable = richtext_wrapper.locator('[contenteditable="true"]')
    assert contenteditable.element_handle() is not None
    return contenteditable


def select_ipsum(paragraph):
    paragraph.evaluate('''paragraph => {
        const selection = window.getSelection();
        const range = document.createRange();
        range.setStart(paragraph.childNodes[0], 6);
        range.setEnd(paragraph.childNodes[0], 11);
        selection.removeAllRanges();
        selection.addRange(range);
    }''')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['new_advertisement'])
@pytest.mark.parametrize('control', [('bold', 'strong'), ('italic', 'em'), ('underline', 'u')])
def test_tiptap_marks(page, viewname, menubar, contenteditable, control):
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    contenteditable.type(lorem)
    select_ipsum(contenteditable.locator('p').element_handle())
    assert contenteditable.inner_html() == f"<p>{lorem}</p>"
    menubar.locator(f'[richtext-toggle="{control[0]}"]').click()
    assert contenteditable.inner_html() == f"<p>{lorem[:6]}<{control[1]}>{lorem[6:11]}</{control[1]}>{lorem[11:]}</p>"
