from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.shortcuts import render
from django import forms
from .models import Payment, MAIBSettings, PaymentLog
from .services import MAIBPaymentService


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


class RefundForm(forms.Form):
    """Form for processing refunds"""
    refund_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Refund Amount',
        help_text='Leave empty for full refund'
    )
    confirm = forms.BooleanField(
        required=True,
        label='I confirm that I want to process this refund'
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'book', 'amount', 'currency', 'status_badge', 'created_at', 'paid_at', 'refund_actions']
    list_filter = ['status', 'currency', 'created_at', 'callback_received']
    search_fields = ['order_id', 'pay_id', 'user__username', 'user__email', 'book__title']
    readonly_fields = [
        'id', 'pay_id', 'order_id', 'pay_url', 'status_code', 'status_message',
        'rrn', 'approval_code', 'card_number', 'three_ds', 'refund_amount',
        'refund_date', 'created_at', 'updated_at', 'paid_at', 'callback_received',
        'callback_data', 'client_ip'
    ]
    date_hierarchy = 'created_at'
    actions = ['process_refund']
    
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

    def refund_actions(self, obj):
        """Display refund action button"""
        if obj.can_refund():
            return format_html(
                '<a class="button" href="{}">Process Refund</a>',
                reverse('admin:payments_payment_refund', args=[obj.pk])
            )
        elif obj.status == 'REFUNDED':
            return format_html(
                '<span style="color: blue;">✓ Refunded: {} MDL</span>',
                obj.refund_amount
            )
        else:
            return format_html('<span style="color: gray;">Not eligible</span>')
    refund_actions.short_description = 'Refund'

    def get_urls(self):
        """Add custom URL for refund page"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/refund/',
                self.admin_site.admin_view(self.refund_view),
                name='payments_payment_refund'
            ),
        ]
        return custom_urls + urls

    def refund_view(self, request, object_id):
        """Custom view for processing refunds"""
        payment = self.get_object(request, object_id)

        if not payment:
            self.message_user(request, 'Payment not found', messages.ERROR)
            return HttpResponseRedirect(reverse('admin:payments_payment_changelist'))

        if not payment.can_refund():
            self.message_user(
                request,
                f'Cannot refund payment with status: {payment.status}',
                messages.ERROR
            )
            return HttpResponseRedirect(
                reverse('admin:payments_payment_change', args=[payment.pk])
            )

        if request.method == 'POST':
            form = RefundForm(request.POST)
            if form.is_valid():
                refund_amount = form.cleaned_data.get('refund_amount')

                # Validate refund amount
                if refund_amount and refund_amount > payment.amount:
                    messages.error(request, f'Refund amount cannot exceed payment amount ({payment.amount} {payment.currency})')
                    return render(request, 'admin/payments/payment/refund.html', {
                        'payment': payment,
                        'form': form,
                        'opts': self.model._meta,
                    })

                # Process refund (determine mode from active settings)
                from .models import MAIBSettings
                active_settings = MAIBSettings.objects.filter(is_active=True).first()
                test_mode = active_settings.mode == 'test' if active_settings else True

                service = MAIBPaymentService(test_mode=test_mode)
                success, result = service.refund_payment(payment, refund_amount)

                if success:
                    messages.success(
                        request,
                        f'Successfully refunded {refund_amount or payment.amount} {payment.currency} for payment {payment.order_id}'
                    )
                    return HttpResponseRedirect(
                        reverse('admin:payments_payment_change', args=[payment.pk])
                    )
                else:
                    error_msg = result.get('error', 'Unknown error')
                    messages.error(request, f'Refund failed: {error_msg}')
        else:
            form = RefundForm()

        context = {
            'payment': payment,
            'form': form,
            'opts': self.model._meta,
            'title': f'Refund Payment: {payment.order_id}',
            'site_title': 'Django admin',
            'site_header': 'Django administration',
        }

        return render(request, 'admin/payments/payment/refund.html', context)

    def process_refund(self, request, queryset):
        """Admin action to refund selected payments"""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one payment to refund', messages.WARNING)
            return

        payment = queryset.first()
        return HttpResponseRedirect(
            reverse('admin:payments_payment_refund', args=[payment.pk])
        )
    process_refund.short_description = 'Process refund for selected payment'

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