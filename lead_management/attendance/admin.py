from django.contrib import admin
from .models import Attendance

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time_in', 'time_out', 'total_hours', 'status')
    list_filter = ('date', 'status', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'

admin.site.register(Attendance, AttendanceAdmin)
