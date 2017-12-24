from django.contrib import admin

from .models import PMT


class PMTAdmin(admin.ModelAdmin):
    list_display = ('filename', 'creation_datetime')


admin.site.register(PMT, PMTAdmin)
