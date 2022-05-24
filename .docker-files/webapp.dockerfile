FROM docker.uibk.ac.at:443/zid/webinfo/python:latest
LABEL Description="django-formset testapp" Maintainer="Jacob Rief"
RUN mkdir /web
WORKDIR /web
ARG DJANGO_WORKDIR=/web/workdir
ARG DJANGO_STATIC_ROOT=/web/staticfiles

# install packages outside of PyPI
RUN apt-get upgrade -y
RUN pip install --upgrade pip

# install project specific requirements
RUN pip install django Pillow django-formset

# copy project relevant files into container
ADD testapp /web/testapp
COPY .docker-files/uwsgi.ini /etc/uwsgi.ini
COPY .docker-files/entrypoint.sh /web/entrypoint.sh

# handle static and media files
ENV DJANGO_STATIC_ROOT=$DJANGO_STATIC_ROOT
ENV DJANGO_WORKDIR=$DJANGO_WORKDIR
ENV DJANGO_SECRET_KEY=dummy_secret_key
RUN mkdir -p $DJANGO_STATIC_ROOT
RUN ./testapp/manage.py collectstatic --noinput

# handle permissions
RUN useradd -M -d /web -s /bin/bash django
RUN chown -R django.django $DJANGO_STATIC_ROOT

EXPOSE 9019

# keep media files in external volume
VOLUME $DJANGO_WORKDIR

ENTRYPOINT ["/web/entrypoint.sh"]
CMD ["uwsgi"]
