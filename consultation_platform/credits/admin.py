from django.contrib import admin
from .models import UserCredit, ProviderCredit, Transaction, Withdrawal

@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__email',)

@admin.register(ProviderCredit)
class ProviderCreditAdmin(admin.ModelAdmin):
    list_display = ('provider', 'balance')
    search_fields = ('provider__user__email',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('user__email', 'description')

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('provider', 'amount', 'status', 'requested_at', 'processed_at')
    list_filter = ('status', 'requested_at', 'processed_at')
    search_fields = ('provider__user__email',)
    actions = ['approve_withdrawals', 'reject_withdrawals']
    
    def approve_withdrawals(self, request, queryset):
        from django.utils import timezone
        for withdrawal in queryset.filter(status=Withdrawal.PENDING):
            provider_credit = ProviderCredit.objects.get(provider=withdrawal.provider)
            if provider_credit.balance >= withdrawal.amount:
                provider_credit.balance -= withdrawal.amount
                provider_credit.save()
                withdrawal.status = Withdrawal.APPROVED
                withdrawal.processed_at = timezone.now()
                withdrawal.save()
    approve_withdrawals.short_description = "Approve selected withdrawals"
    
    def reject_withdrawals(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status=Withdrawal.PENDING).update(
            status=Withdrawal.REJECTED,
            processed_at=timezone.now()
        )
    reject_withdrawals.short_description = "Reject selected withdrawals"
