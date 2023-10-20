FROM python:3.11
LABEL Description="django-formset testapp" Maintainer="Jacob Rief"
RUN mkdir /web
WORKDIR /web

# install packages outside of PyPI
RUN apt-get upgrade -y
RUN apt-get install -y ca-certificates curl make gnupg
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update
RUN apt-get install -y nodejs
RUN pip install --upgrade pip

# install Node specific requirements
COPY package.json /web/package.json
COPY package-lock.json /web/package-lock.json
RUN npm ci

# install Python specific requirements
RUN pip install django psycopg2-binary Pillow uWSGI docutils Sphinx sphinx-toolbox furo
RUN pip install https://github.com/jrief/django-sphinx-view/archive/refs/heads/main.zip

# copy project relevant files into container
ADD assets /web/assets
ADD client /web/client
ADD docs /web/docs
ADD formset /web/formset
ADD testapp /web/testapp
COPY .deployment/uwsgi.ini /etc/uwsgi.ini
COPY .deployment/entrypoint.sh /web/entrypoint.sh

# compile assets
RUN npm run tag-attributes
RUN npm run compilescss
RUN npm run tailwindcss
RUN npm run esbuild

# create documentation
RUN npm run docscss
RUN make --directory=docs json

# handle static and media files
ENV DJANGO_STATIC_ROOT=/web/staticfiles
ENV DJANGO_WORKDIR=/web/workdir
ENV DJANGO_MEDIA_ROOT=/web/workdir/media
ENV DJANGO_SECRET_KEY=dummy_secret_key
ENV PYTHONPATH=/web
RUN mkdir -p $DJANGO_STATIC_ROOT
RUN DJANGO_DEPLOYED=1 ./testapp/manage.py collectstatic --noinput

# handle permissions
RUN useradd -M -d /web -s /bin/bash django
RUN chown -R django.django $DJANGO_STATIC_ROOT

EXPOSE 8080

ENTRYPOINT ["/web/entrypoint.sh"]
CMD ["uwsgi"]
