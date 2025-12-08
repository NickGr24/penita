from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, MAIBSettings, PaymentLog


@admin.register(MAIBSettings)
class MAIBSettingsAdmin(admin.ModelAdmin):
    list_display = ['mode', 'is_active', 'created_at', 'updated_at']
    list_filter = ['mode', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('mode', 'is_active', 'api_base_url')
        }),
        ('Credentials', {
            'fields': ('project_id', 'project_secret', 'signature_key'),
            'description': 'These credentials are provided by MAIB'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # If setting this as active, deactivate others in the same mode
        if obj.is_active:
            MAIBSettings.objects.filter(mode=obj.mode, is_active=True).exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'book', 'amount', 'currency', 'status_badge', 'created_at', 'paid_at']
    list_filter = ['status', 'currency', 'created_at', 'callback_received']
    search_fields = ['order_id', 'pay_id', 'user__username', 'user__email', 'book__title']
    readonly_fields = [
        'id', 'pay_id', 'order_id', 'pay_url', 'status_code', 'status_message',
        'rrn', 'approval_code', 'card_number', 'three_ds', 'refund_amount',
        'refund_date', 'created_at', 'updated_at', 'paid_at', 'callback_received',
        'callback_data', 'client_ip'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('id', 'user', 'book', 'amount', 'currency', 'status', 'description')
        }),
        ('MAIB Details', {
            'fields': ('pay_id', 'order_id', 'pay_url', 'status_code', 'status_message'),
            'classes': ['collapse']
        }),
        ('Payment Details', {
            'fields': ('rrn', 'approval_code', 'card_number', 'three_ds', 'client_ip'),
            'classes': ['collapse']
        }),
        ('Refund Info', {
            'fields': ('refund_amount', 'refund_date'),
            'classes': ['collapse']
        }),
        ('Callback Data', {
            'fields': ('callback_received', 'callback_data'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ['collapse']
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'OK': 'green',
            'FAIL': 'red',
            'CANCELLED': 'gray',
            'REFUNDED': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        # Prevent manual payment creation through admin
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent payment deletion
        return False
    
    class PaymentLogInline(admin.TabularInline):
        model = PaymentLog
        extra = 0
        readonly_fields = ['log_type', 'message', 'data', 'created_at']
        can_delete = False
        
        def has_add_permission(self, request, obj=None):
            return False
    
    inlines = [PaymentLogInline]


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'payment', 'log_type', 'message_preview']
    list_filter = ['log_type', 'created_at']
    search_fields = ['message', 'payment__order_id', 'payment__pay_id']
    readonly_fields = ['payment', 'log_type', 'message', 'data', 'created_at']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False