#!/usr/bin/env python
from setuptools import setup, find_packages
from formset import __version__


with open('README.md') as fh:
    long_description = fh.read()


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Framework :: Django :: 4.0',
    'Framework :: Django :: 4.1',
]

setup(
    name='django-formset',
    version=__version__,
    description='Prevalidate Django Forms in the browser',
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    url='https://github.com/jrief/django-formset',
    packages=find_packages(exclude=['testapp', 'docs']),
    install_requires=[
        'django>=4.0',
    ],
    extra_requires={
        'thumbnail': ['Pillow'],
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
