from django.contrib import admin
from .models import Lead, LeadSource, Interaction


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 0
    fields = ('interaction_type', 'date_time', 'summary', 'created_by')
    readonly_fields = ('created_by',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company', 'email', 'phone', 'status', 'stage', 'assigned_to', 'created_at')
    list_filter = ('status', 'stage', 'source', 'assigned_to', 'converted_to_client')
    search_fields = ('first_name', 'last_name', 'company', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'company', 'position', 'email', 'phone', 'address')
        }),
        ('Lead Details', {
            'fields': ('source', 'notes', 'status', 'stage', 'estimated_value', 'probability', 'converted_to_client')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by', 'next_follow_up')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [InteractionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when the object is first created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Interaction):
                if not instance.pk:  # New interaction
                    instance.created_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('lead', 'interaction_type', 'date_time', 'summary', 'created_by')
    list_filter = ('interaction_type', 'date_time', 'created_by')
    search_fields = ('lead__first_name', 'lead__last_name', 'summary', 'details')
    readonly_fields = ('created_at', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when the object is first created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
