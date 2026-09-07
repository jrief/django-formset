from django import template

register = template.Library()


@register.simple_tag
def page_url(page_id):
    from testapp.models import PageModel

    page = PageModel.objects.get(pk=page_id)
    return page.get_absolute_url()
