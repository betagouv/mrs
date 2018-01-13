from django.contrib import admin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .views import MRSRequestUpdateView
from .models import MRSRequest

csrf_protect_m = method_decorator(csrf_protect)


class MRSRequestAdmin(admin.ModelAdmin):
    list_display = (
        'verbose_id',
        'insured_first_name',
        'insured_last_name',
        'insured_nir',
        'status',
    )
    search_fields = (
        'insured__first_name',
        'insured__last_name',
        'insured__email',
        'insured__nir',
        'form_id',
    )
    list_filter = (
        'status',
    )

    def insured_first_name(self, obj):
        if obj.insured:
            return obj.insured.first_name
    insured_first_name.admin_order_field = 'insured__first_name'

    def insured_last_name(self, obj):
        if obj.insured:
            return obj.insured.last_name
    insured_last_name.admin_order_field = 'insured__last_name'

    def insured_nir(self, obj):
        if obj.insured:
            return obj.insured.nir
    insured_nir.admin_order_field = 'insured__nir'

    @csrf_protect_m
    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        return MRSRequestUpdateView.as_view(mrsrequest_uuid=object_id)(request)

admin.site.register(MRSRequest, MRSRequestAdmin)
