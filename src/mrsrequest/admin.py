from django.contrib import admin

from .models import MRSRequest


class MRSRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(MRSRequest, MRSRequestAdmin)
