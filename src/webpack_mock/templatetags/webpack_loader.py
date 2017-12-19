"""Mock for render_bundle, activate by settings if npm is not in path."""


from django import template

register = template.Library()


@register.simple_tag
def render_bundle(bundle_name, extension=None, config='DEFAULT', attrs=''):
    return ''
