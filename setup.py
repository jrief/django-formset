#!/usr/bin/env python
from setuptools import setup, find_namespace_packages
from formset import __version__


with open('README.md') as fh:
    long_description = fh.read()


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Framework :: Django :: 5.0',
    'Framework :: Django :: 5.1',
    'Framework :: Django :: 5.2',
]

setup(
    name='django-formset',
    version=__version__,
    description='The missing widgets and form manipulation library for Django',
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    url='https://django-formset.fly.dev/',
    packages=find_namespace_packages(include=['formset']),
    install_requires=[
        'django>=5.0',
    ],
    extra_requires={
        'thumbnail': ['Pillow'],
        'phonenumbers': ['phonenumbers'],
    },
    license='MIT',
    platforms=['OS Independent'],
    keywords=['Django Forms', 'webcomponent'],
    classifiers=CLASSIFIERS,
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=False,
)
