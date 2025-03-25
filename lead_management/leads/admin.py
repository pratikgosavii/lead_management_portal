from django.contrib import admin
from .models import Lead, LeadSource, LeadStatus

class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'email', 'source', 'status', 'assigned_to', 'created_at')
    list_filter = ('source', 'status', 'assigned_to', 'created_at')
    search_fields = ('name', 'company', 'phone', 'email')
    date_hierarchy = 'created_at'

admin.site.register(Lead, LeadAdmin)
admin.site.register(LeadSource)
admin.site.register(LeadStatus)
