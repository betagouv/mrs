from django import template

from mrsrequest.models import MRSRequest

register = template.Library()


@register.simple_tag
def mrsrequest_new_count():
    return MRSRequest.objects.filter(status=0).count()


@register.simple_tag
def mrsrequest_validated_count():
    return MRSRequest.objects.filter(status=1).count()


@register.simple_tag
def mrsrequest_rejected_count():
    return MRSRequest.objects.filter(status=2).count()


@register.simple_tag
def mrsrequest_total_count():
    return MRSRequest.objects.all().count()
