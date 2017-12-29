from django.contrib import admin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from transport.models import Transport

from .views import MRSRequestUpdateView
from .models import MRSRequest

csrf_protect_m = method_decorator(csrf_protect)


class TransportInline(admin.StackedInline):
    model = Transport
    extra = 0


class MRSRequestAdmin(admin.ModelAdmin):
    inlines = (
        TransportInline,
    )

    list_display = (
        'creation_datetime',
        'insured',
        'status',
    )
    search_fields = (
        'insured__first_name',
        'insured__last_name',
        'insured__email',
    )
    list_filter = (
        'status',
    )

    @csrf_protect_m
    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        return MRSRequestUpdateView.as_view(mrsrequest_uuid=object_id)(request)

admin.site.register(MRSRequest, MRSRequestAdmin)
