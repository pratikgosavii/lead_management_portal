from django.contrib import admin
from .models import Project, ProjectStatus

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'start_date', 'end_date', 'status', 'budget', 'created_at')
    list_filter = ('status', 'start_date', 'end_date', 'created_at')
    search_fields = ('name', 'description', 'client__name', 'client__company')
    date_hierarchy = 'created_at'

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectStatus)
