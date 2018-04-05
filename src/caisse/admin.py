from django.contrib import admin

from .models import Caisse, Email


class CaisseAdmin(admin.ModelAdmin):
    readonly_fields = ('score',)
    list_display = ('code', 'name', 'number', 'active', 'score')
    search_fields = ('code', 'name', 'number')
    list_filter = ('active', 'score')


admin.site.register(Caisse, CaisseAdmin)


class EmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'caisse')


admin.site.register(Email, EmailAdmin)
