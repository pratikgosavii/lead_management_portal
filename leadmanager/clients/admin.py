from django.contrib import admin
from .models import Client, ClientContact

class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'relationship_manager', 'status', 'created_at')
    list_filter = ('status', 'relationship_manager', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'lead_source')
    inlines = [ClientContactInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'website', 'address')
        }),
        ('Relationship', {
            'fields': ('relationship_manager', 'status', 'industry', 'lead_source')
        }),
        ('Notes & Timestamps', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'position', 'email', 'phone', 'is_primary')
    list_filter = ('client', 'is_primary')
    search_fields = ('name', 'email', 'phone', 'client__name')
