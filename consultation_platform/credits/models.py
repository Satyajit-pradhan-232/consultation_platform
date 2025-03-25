
from django.db import models
from users.models import User
from providers.models import Provider
from django.utils import timezone

class UserCredit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.email} - {self.balance} credits"

class ProviderCredit(models.Model):
    provider = models.OneToOneField(Provider, on_delete=models.CASCADE, related_name='credit')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.provider.user.email} - {self.balance} credits"

class Transaction(models.Model):
    PURCHASE = 'purchase'
    CONSULTATION = 'consultation'
    TRANSACTION_TYPES = [
        (PURCHASE, 'Purchase'),
        (CONSULTATION, 'Consultation'),
    ]

    # Transaction statuses
    QUEUED = 'queued'
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (QUEUED, 'Queued'),
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=QUEUED)
    # For payment gateway reference
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"

class Withdrawal(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    payment_details = models.JSONField(default=dict)  # For storing bank account or payment method details
    
    def __str__(self):
        return f"{self.provider.user.email} - {self.amount} - {self.status}"
