from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'sender', 'timestamp')
    list_filter = ('consultation', 'sender')
    search_fields = ('consultation__user__email', 'consultation__provider__user__email', 'sender__email')