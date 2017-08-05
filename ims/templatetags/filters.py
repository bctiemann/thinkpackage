from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def format_newlines(value):
    return value.replace('\n', '<br />')

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def add(value, arg):
    return value + arg
