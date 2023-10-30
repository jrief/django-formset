from django.template import Template, Context


def test_format_phonenumber():
    template = Template('{% load phonenumber %}{{ value|format_phonenumber }}')
    context = Context({'value': '+49301234567'})
    assert template.render(context) == '+49 30 1234567'


def test_format_national_phonenumber():
    template = Template('{% load phonenumber %}{{ value|format_phonenumber:"national" }}')
    context = Context({'value': '+12121234567'})
    assert template.render(context) == '(212) 123-4567'


def test_format_international_phonenumber():
    template = Template('{% load phonenumber %}{{ value|format_phonenumber:"international" }}')
    context = Context({'value': '+442012345678'})
    assert template.render(context) == '+44 20 1234 5678'
