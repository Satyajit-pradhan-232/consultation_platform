from django.db import models
from users.models import User
from providers.models import Provider
from django.utils import timezone
from django.core.exceptions import ValidationError

class Consultation(models.Model):
    REQUESTED = 'requested'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (REQUESTED, 'Requested'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (ONGOING, 'Ongoing'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_consultations')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='provider_consultations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=REQUESTED)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Consultation: {self.user.email} - {self.provider.user.email} ({self.status})"
    
    def clean(self):
      # Check for overlapping consultations for both user and provider (only when status is accepted)
        if self.status == self.ACCEPTED and self.start_time:
            overlapping_user_consultations = Consultation.objects.filter(
                user=self.user,
                status=self.ACCEPTED,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(pk=self.pk)  # Exclude the current consultation if updating

            overlapping_provider_consultations = Consultation.objects.filter(
                provider=self.provider,
                status=self.ACCEPTED,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(pk=self.pk)

            if overlapping_user_consultations.exists() or overlapping_provider_consultations.exists():
                raise ValidationError("User or Provider has overlapping consultations.")
            
    def save(self, *args, **kwargs):
        if self.status == self.ACCEPTED and self.start_time is None:
            self.start_time = timezone.now()
        # No end time is automatically updated to avoid clashing times in the clean() method
        super().save(*args, **kwargs)