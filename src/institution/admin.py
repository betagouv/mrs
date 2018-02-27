from django.contrib import admin

from .models import Institution


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('finess', 'origin')


admin.site.register(Institution, InstitutionAdmin)
