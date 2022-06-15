import json
import pytest
import re
from pathlib import Path
from time import sleep

from django.conf import settings
from django.core.signing import get_cookie_signer
from django.urls import path

from formset.views import FormView

from .forms.upload import UploadForm


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    form_class=UploadForm
    success_url = '/success'


urlpatterns = [path('upload', DemoFormView.as_view(), name='upload')]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_image(page, mocker):
    choose_file_button = page.query_selector('django-formset form button.dj-choose-file')
    assert choose_file_button is not None  # that button would open the file selector
    dropbox = page.query_selector('django-formset form figure.dj-dropbox')
    assert dropbox.inner_html() == '<div class="dj-empty-item">Drag file here</div>'
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    img_element = dropbox.wait_for_selector('img')
    assert img_element is not None
    img_src = img_element.get_attribute('src')
    match = re.match(r'^/media/((upload_temp/python-django\.[a-z0-9_]+?)_h128(.png))$', img_src)
    assert match is not None
    thumbnail_url = match.group(1)
    assert (settings.MEDIA_ROOT / thumbnail_url).exists()  # the thumbnail
    thumbnail_url = f'/media/{thumbnail_url}'
    download_url = match.group(2) + match.group(3)
    assert (settings.MEDIA_ROOT / download_url).exists()  # the uploaded file
    download_url = f'/media/{download_url}'
    figcaption = dropbox.query_selector('figcaption')
    assert figcaption is not None
    description_lists = figcaption.query_selector_all('dl')
    assert len(description_lists) == 3
    assert description_lists[0].inner_html() == '<dt>Name:</dt><dd>python-django.png</dd>'
    assert description_lists[1].inner_html() == '<dt>Content-Type:</dt><dd>image/png</dd>'
    assert description_lists[2].inner_html() == '<dt>Size:</dt><dd>16001</dd>'
    button = dropbox.query_selector('a.dj-delete-file')
    assert button is not None
    assert button.inner_text() == 'Delete'
    button = dropbox.query_selector('a.dj-download-file')
    assert button is not None
    assert button.get_attribute('download') == 'python-django.png'
    assert button.get_attribute('href') == download_url
    spy = mocker.spy(DemoFormView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    file = request['formset_data']['avatar'][0]
    signer = get_cookie_signer(salt='formset')
    upload_temp_name = signer.unsign(file['upload_temp_name'])
    assert (settings.MEDIA_ROOT / upload_temp_name).exists()
    assert file['name'] == 'python-django.png'
    assert file['download_url'] == download_url
    assert file['thumbnail_url'] == thumbnail_url
    assert file['content_type'] == 'image/png'
    assert file['size'] == 16001
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_pdf(page):
    page.set_input_files('#id_avatar', 'testapp/assets/dummy.pdf')
    dropbox = page.query_selector('django-formset form django-field-group figure.dj-dropbox')
    assert dropbox is not None
    img_src = dropbox.wait_for_selector('img').get_attribute('src')
    assert img_src == '/static/formset/icons/file-pdf.svg'


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_broken_image(page):
    page.set_input_files('#id_avatar', 'testapp/assets/broken-image.jpg')
    dropbox = page.query_selector('django-formset form django-field-group figure.dj-dropbox')
    assert dropbox is not None
    img_src = dropbox.wait_for_selector('img').get_attribute('src')
    assert img_src == '/static/formset/icons/file-picture.svg'


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_required(page):
    field_group = page.query_selector('django-formset django-field-group')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    error_placeholder = field_group.wait_for_selector('.dj-errorlist .dj-placeholder')
    assert error_placeholder.inner_html() == "This field is required."


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_delete_uploaded_file(page):
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    dropbox = page.query_selector('django-formset form django-field-group figure.dj-dropbox')
    dropbox.wait_for_selector('img')
    delete_button = dropbox.wait_for_selector('figcaption a.dj-delete-file')
    delete_button.click()
    empty_item = dropbox.wait_for_selector('div.dj-empty-item')
    assert empty_item.inner_html() == "Drag file here"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_progressbar(page):
    field_group = page.query_selector('django-formset django-field-group')
    client = page.context.new_cdp_session(page)
    client.send('Network.enable')
    network_conditions = {
        'offline': False,
        'downloadThroughput': 999999,
        'uploadThroughput': 9999,
        'latency': 20
    }
    client.send('Network.emulateNetworkConditions', network_conditions)
    test_image_path = Path('testapp/assets/python-django.png')
    assert test_image_path.exists()
    assert test_image_path.stat().st_size == 16001
    file_uploader = field_group.query_selector('#id_avatar')
    assert file_uploader is not None
    file_uploader.set_input_files([test_image_path])
    progress_bar = field_group.wait_for_selector('progress')
    assert progress_bar is not None
    progress_value = float(progress_bar.get_attribute('value'))
    assert progress_value >= 0.0 and progress_value <= 1.0
    sleep(0.2)
    progress_value = float(progress_bar.get_attribute('value'))
    assert progress_value > 0.0 and progress_value <= 1.0
    # thumbnailing image takes some time
    img_element = field_group.wait_for_selector('figure.dj-dropbox img')
    assert img_element is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_in_progress(page):
    field_group = page.wait_for_selector('django-formset django-field-group')
    client = page.context.new_cdp_session(page)
    client.send('Network.enable')
    network_conditions = {
        'offline': False,
        'downloadThroughput': 999999,
        'uploadThroughput': 512,
        'latency': 20
    }
    client.send('Network.emulateNetworkConditions', network_conditions)
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    sleep(0.02)
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    error_placeholder = field_group.wait_for_selector('.dj-errorlist .dj-placeholder')
    assert error_placeholder.inner_html() == "File upload still in progress."


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_interupt_upload(page):
    def handle_route(route):
        sleep(0.01)
        route.abort()

    field_group = page.query_selector('django-formset django-field-group')
    page.context.route('/upload', handle_route)
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    sleep(0.02)
    error_placeholder = field_group.wait_for_selector('.dj-errorlist .dj-placeholder')
    assert error_placeholder.inner_html() == "File upload failed."
