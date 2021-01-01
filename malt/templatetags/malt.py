from django import template

register = template.Library()


@register.filter
def append(value, arg):
    if value:
        return '{}/{}'.format(value, arg)
    else:
        return arg
