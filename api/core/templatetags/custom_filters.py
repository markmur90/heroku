# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def startswith(text, prefix):
    return text.startswith(prefix)
