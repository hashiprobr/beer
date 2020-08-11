from django import template

register = template.Library()


@register.filter
def append(value, arg):
    if value is None:
        return arg
    else:
        return '{}/{}'.format(value, arg)
