from django.contrib import admin
from .models import Client

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'email', 'converted_from_lead', 'created_at')
    list_filter = ('created_at',)  # Removed converted_from_lead from list_filter since it's a method
    search_fields = ('name', 'company', 'phone', 'email')
    date_hierarchy = 'created_at'

admin.site.register(Client, ClientAdmin)
