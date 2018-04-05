from django.contrib import admin
from django.db.models import Count

from .models import EmailTemplate


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'subject',
        'requests',
        'active',
    ]
    list_display_links = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            requests=Count('mrsrequest'))

    def requests(self, obj):
        return obj.requests
    requests.admin_order_field = 'requests'
    requests.short_description = 'Demandes'

    def has_delete_permission(self, *args, **kwargs):
        return False

admin.site.register(EmailTemplate, EmailTemplateAdmin)
