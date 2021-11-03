from django import template
from django.template.defaultfilters import stringfilter
from django.template.base import Node

import logging
logger = logging.getLogger(__name__)

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


@register.filter
def split_path(value):
    return value.split('/')


@register.simple_tag
def is_authorized_for_client(user, client):
    return user.is_authorized_for_client(client)


class LogCsrfTokenNode(Node):
    def render(self, context):
        csrf_token = context.get('csrf_token')
        logger.info(csrf_token)
        return ''


@register.tag
def log_csrf_token(parser, token):
    return LogCsrfTokenNode()
