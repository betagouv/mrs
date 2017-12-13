from django.contrib import admin

from .models import Bill, Transport


admin.site.register(Bill)
admin.site.register(Transport)
