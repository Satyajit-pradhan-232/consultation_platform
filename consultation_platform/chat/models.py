from django.db import models
from users.models import User
from consultations.models import Consultation
from django.utils import timezone

class ChatMessage(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.JSONField() # Store the entire message as JSON (including timestamp, etc.) to allow for future extensibility
    timestamp  = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.sender.email} : {self.message}'

    class Meta:
        ordering = ['timestamp']