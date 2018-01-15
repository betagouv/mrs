from django.contrib import admin

from .forms import PersonForm
from .models import Person


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'nir',
        'first_name',
        'last_name',
        'birth_date',
        'email',
    )
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'nir',
    )
    form = PersonForm
admin.site.register(Person, PersonAdmin)
