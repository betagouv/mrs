from django.contrib import admin

from .models import Bill, Transport


class BillAdmin(admin.ModelAdmin):
    list_display = ('filename', 'creation_datetime')

admin.site.register(Bill, BillAdmin)


class TransportAdmin(admin.ModelAdmin):
    list_display = ('mrsrequest', 'date_depart', 'date_return', 'expense')

admin.site.register(Transport, TransportAdmin)
