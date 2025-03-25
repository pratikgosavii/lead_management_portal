from django.contrib import admin
from .models import Client

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'email', 'converted_from_lead', 'created_at')
    list_filter = ('created_at', 'converted_from_lead')
    search_fields = ('name', 'company', 'phone', 'email')
    date_hierarchy = 'created_at'

admin.site.register(Client, ClientAdmin)
