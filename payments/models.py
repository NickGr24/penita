from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from django.utils import timezone
import uuid


class MAIBSettings(models.Model):
    """Store MAIB API configuration"""
    MODE_CHOICES = (
        ('test', 'Test/Sandbox'),
        ('production', 'Production'),
    )
    
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='test')
    project_id = models.CharField(max_length=255, help_text="MAIB Project ID")
    project_secret = models.CharField(max_length=255, help_text="MAIB Project Secret")
    signature_key = models.CharField(max_length=255, help_text="Signature Key for callback validation")
    api_base_url = models.URLField(default="https://api.maibmerchants.md/v1")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "MAIB Settings"
        verbose_name_plural = "MAIB Settings"
        
    def __str__(self):
        return f"MAIB {self.mode} - {'Active' if self.is_active else 'Inactive'}"


class Payment(models.Model):
    """Store payment transactions"""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('OK', 'Successful'),
        ('FAIL', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    )
    
    # Internal fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='payments')
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MDL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # MAIB specific fields
    pay_id = models.CharField(max_length=255, unique=True, null=True, blank=True, 
                              help_text="Transaction ID from MAIB")
    order_id = models.CharField(max_length=255, null=True, blank=True,
                                help_text="Our order ID sent to MAIB")
    pay_url = models.URLField(null=True, blank=True, 
                              help_text="Payment URL from MAIB")
    
    # Response data from MAIB
    status_code = models.CharField(max_length=10, null=True, blank=True)
    status_message = models.TextField(null=True, blank=True)
    rrn = models.CharField(max_length=50, null=True, blank=True, 
                          help_text="Retrieval Reference Number")
    approval_code = models.CharField(max_length=50, null=True, blank=True)
    card_number = models.CharField(max_length=20, null=True, blank=True, 
                                   help_text="Masked card number")
    three_ds = models.CharField(max_length=20, null=True, blank=True,
                               help_text="3D Secure status")
    
    # Refund fields
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    callback_received = models.BooleanField(default=False)
    callback_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'book', 'status']),
            models.Index(fields=['pay_id']),
            models.Index(fields=['status', 'created_at']),
        ]
        
    def __str__(self):
        return f"Payment {self.order_id} - {self.user.username} - {self.book.title} - {self.status}"
    
    def is_successful(self):
        return self.status == 'OK'
    
    def mark_as_paid(self):
        """Mark payment as successful"""
        self.status = 'OK'
        self.paid_at = timezone.now()
        self.save()
        
    def can_refund(self):
        """Check if payment can be refunded"""
        return self.status == 'OK' and not self.refund_date


class PaymentLog(models.Model):
    """Log all payment-related activities for debugging"""
    LOG_TYPE_CHOICES = (
        ('request', 'API Request'),
        ('response', 'API Response'),
        ('callback', 'Callback'),
        ('error', 'Error'),
        ('info', 'Info'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, 
                                related_name='logs', null=True, blank=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.log_type} - {self.created_at}"