from django.contrib import admin
from .models import Payment, PaymentMethod

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'payment_date', 'payment_method', 'created_at')
    list_filter = ('payment_date', 'payment_method', 'created_at')
    search_fields = ('project__name', 'description', 'reference_number')
    date_hierarchy = 'payment_date'

admin.site.register(Payment, PaymentAdmin)
admin.site.register(PaymentMethod)
