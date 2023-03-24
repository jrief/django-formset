import json
import pytest
import re
from pathlib import Path
from playwright.sync_api import expect
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
def test_upload_image(page, mocker, viewname):
    choose_file_button = page.locator('django-formset .dj-form button.dj-choose-file')
    expect(choose_file_button).to_be_visible()  # that button would open the file selector
    dropbox = page.locator('django-formset .dj-form figure.dj-dropbox')
    expect(dropbox.locator('div.dj-empty-item')).to_have_text("Drag file here")
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    img_element = dropbox.locator('img')
    expect(img_element).to_be_visible()
    img_src = img_element.get_attribute('src')
    match = re.match(r'^/media/((upload_temp/python-django\.[a-z0-9_]+?)_h128(.png))$', img_src)
    assert match is not None
    thumbnail_url = match.group(1)
    assert (settings.MEDIA_ROOT / thumbnail_url).exists()  # the thumbnail
    thumbnail_url = f'/media/{thumbnail_url}'
    download_url = match.group(2) + match.group(3)
    assert (settings.MEDIA_ROOT / download_url).exists()  # the uploaded file
    download_url = f'/media/{download_url}'
    figcaption = dropbox.locator('figcaption')
    expect(figcaption).to_be_visible()
    description_lists = figcaption.locator('dl')
    expect(description_lists).to_have_count(3)
    expect(description_lists.locator('dt')).to_have_text(["Name:", "Content-Type:", "Size:"])
    expect(description_lists.locator('dd')).to_have_text(["python-django.png", "image/png", "16001"])
    button = dropbox.locator('a.dj-delete-file')
    expect(button).to_be_visible()
    expect(button).to_have_text("Delete")
    button = dropbox.locator('a.dj-download-file')
    expect(button).to_be_visible()
    expect(button).to_have_attribute('download', 'python-django.png')
    expect(button).to_have_attribute('href', download_url)
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
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
def test_upload_pdf(page, viewname):
    dropbox = page.locator('django-formset .dj-form django-field-group figure.dj-dropbox')
    expect(dropbox).to_be_visible()
    page.set_input_files('#id_avatar', 'testapp/assets/dummy.pdf')
    expect(dropbox.locator('img')).to_have_attribute('src', '/static/formset/icons/file-pdf.svg')
    expect(dropbox.locator('figcaption')).to_contain_text("Content-Type:application/pdf")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_broken_image(page, viewname):
    dropbox = page.locator('django-formset .dj-form django-field-group figure.dj-dropbox')
    expect(dropbox).to_be_visible()
    expect(dropbox.locator('figcaption')).not_to_be_visible()
    page.set_input_files('#id_avatar', 'testapp/assets/broken-image.jpg')
    expect(dropbox.locator('img')).to_have_attribute('src', '/static/formset/icons/file-picture.svg')
    expect(dropbox.locator('figcaption')).to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_required(page, viewname):
    field_group = page.locator('django-formset django-field-group')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    error_placeholder = field_group.locator('.dj-errorlist .dj-placeholder')
    expect(error_placeholder).to_have_text("This field is required.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_delete_uploaded_file(page, viewname):
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    dropbox = page.locator('django-formset .dj-form django-field-group figure.dj-dropbox')
    expect(dropbox.locator('img')).to_be_visible()
    delete_button = dropbox.locator('figcaption a.dj-delete-file')
    delete_button.click()
    empty_item = dropbox.locator('div.dj-empty-item')
    expect(empty_item).to_have_text("Drag file here")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_progressbar(page, viewname):
    field_group = page.locator('django-formset django-field-group')
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
    file_uploader = field_group.locator('#id_avatar')
    expect(file_uploader).not_to_be_visible()
    file_uploader.set_input_files([test_image_path])
    progress_bar = field_group.locator('progress')
    expect(progress_bar).not_to_be_visible()
    progress_value = float(progress_bar.get_attribute('value'))
    assert progress_value >= 0.0 and progress_value <= 1.0
    sleep(0.2)
    progress_value = float(progress_bar.get_attribute('value'))
    assert progress_value > 0.0 and progress_value <= 1.0
    # thumbnailing image takes some time
    img_element = field_group.locator('figure.dj-dropbox img')
    expect(img_element).to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_in_progress(page):
    field_group = page.locator('django-formset django-field-group')
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
    page.locator('django-formset').evaluate('elem => elem.submit()')
    error_placeholder = field_group.locator('.dj-errorlist .dj-placeholder')
    expect(error_placeholder).to_have_text("File upload still in progress.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_interupt_upload(page, viewname):
    def handle_route(route):
        sleep(0.01)
        route.abort()

    client = page.context.new_cdp_session(page)
    client.send('Network.enable')
    network_conditions = {
        'offline': False,
        'downloadThroughput': 9999,
        'uploadThroughput': 999,
        'latency': 20
    }
    client.send('Network.emulateNetworkConditions', network_conditions)
    field_group = page.locator('django-formset django-field-group')
    page.context.route('/upload', handle_route)
    page.set_input_files('#id_avatar', 'testapp/assets/python-django.png')
    sleep(0.2)
    error_placeholder = field_group.locator('.dj-errorlist .dj-placeholder')
    expect(error_placeholder).to_have_text("File upload failed.")
