from django.contrib import admin

from .models import Customer, Seller


class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email', 'phone')
    ordering = ('name',)


admin.site.register(Customer, PersonAdmin)
admin.site.register(Seller, PersonAdmin)
