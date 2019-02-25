from django import template


register = template.Library()


@register.filter
def is_half(value):
    return value and not int(value) % 2
