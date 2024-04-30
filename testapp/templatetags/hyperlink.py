from django import template

from testapp.models import PageModel

register = template.Library()


@register.simple_tag
def page_url(page_id):
    page = PageModel.objects.get(pk=page_id)
    return page.get_absolute_url()
