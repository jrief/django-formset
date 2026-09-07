from django import VERSION as DJANGO_VERSION
from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = template.Library()


@register.tag(name="submit_row")
def submit_row_tag(parser, token):
    if DJANGO_VERSION < (6, 1):
        return InclusionAdminNode(parser, token, func=submit_row, template_name="formset/submit_line.html")
    else:
        return InclusionAdminNode(
            "submit_row", parser, token, func=submit_row, template_name="formset/submit_line.html"
        )


@register.tag(name="change_form_object_tools")
def change_form_object_tools_tag(parser, token):
    """Display the row of change form object tools."""
    if DJANGO_VERSION < (6, 1):
        return InclusionAdminNode(
            parser,
            token,
            func=lambda context: context,
            template_name="change_form_object_tools.html",
        )
    else:
        return InclusionAdminNode(
            "change_form_object_tools",
            parser,
            token,
            func=lambda context: context,
            template_name="change_form_object_tools.html",
        )
