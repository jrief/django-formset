import json
import os
import pytest
import re
from time import sleep

from django.core.signing import get_cookie_signer
from django.forms import fields, Form
from django.urls import path

from formset.views import FormsetView
from formset.widgets import UploadedFileInput


class UploadForm(Form):
    name = 'upload'

    file = fields.FileField(
        label="Choose file",
        widget=UploadedFileInput,
        required=True,
    )


view = FormsetView.as_view(
    template_name='tests/form_with_button.html',
    form_class=UploadForm,
    success_url='/success',
)


urlpatterns = [path('upload', view, name='upload')]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['upload'])
def test_upload_file(page, mocker):
    choose_file_button = page.query_selector('django-formset form button.dj-choose-file')
    assert choose_file_button is not None # that button would open the file selector
    dropbox = page.query_selector('django-formset form ul.dj-dropbox')
    assert dropbox.inner_html() == '<li class="dj-empty-item">Drag file here</li>'
    page.set_input_files('django-formset form input#id_file', 'testapp/assets/python-django.png')
    sleep(0.1)
    file_picture = dropbox.query_selector('li.dj-file-picture')
    assert file_picture is not None
    img_src = file_picture.query_selector('img').get_attribute('src')
    print(img_src)
    match = re.match(r'^/((media/upload_temp/python-django\.[a-z0-9_]+?)_154x128(.png))$', img_src)
    assert match is not None
    thumbnail_url = match.group(1)
    assert os.path.exists(thumbnail_url)  # the thumbnail
    thumbnail_url = f'/{thumbnail_url}'
    download_url = match.group(2) + match.group(3)
    assert os.path.exists(download_url)  # the uploaded file
    download_url = f'/{download_url}'
    file_caption = dropbox.query_selector('li.dj-file-caption')
    assert file_caption is not None
    figures = file_caption.query_selector_all('figure')
    assert len(figures) == 3
    assert figures[0].inner_html() == '<figcaption>Name:</figcaption><p>python-django.png</p>'
    assert figures[1].inner_html() == '<figcaption>Content-Type:</figcaption><p>image/png</p>'
    assert figures[2].inner_html() == '<figcaption>Size:</figcaption><p>16001</p>'
    button = file_caption.query_selector('a.dj-delete-file')
    assert button is not None
    assert button.inner_text() == 'Delete'
    button = file_caption.query_selector('a.dj-download-file')
    assert button is not None
    assert button.get_attribute('download') == 'python-django.png'
    assert button.get_attribute('href') == download_url
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    file = request['upload']['file'][0]
    signer = get_cookie_signer(salt='formset')
    upload_temp_name = signer.unsign(file['upload_temp_name'])
    assert os.path.exists(f'media/{upload_temp_name}')
    assert file['name'] == 'python-django.png'
    assert file['download_url'] == download_url
    assert file['thumbnail_url'] == thumbnail_url
    assert file['content_type'] == 'image/png'
    assert file['size'] == 16001
    assert spy.spy_return.status_code == 200
