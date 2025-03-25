from rest_framework import serializers
from .models import UserCredit, ProviderCredit, Transaction, Withdrawal
from providers.models import Provider

class UserCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCredit
        fields = ['balance']
        read_only_fields = ['balance']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount','status', 'transaction_type', 'description', 'timestamp', 'reference_id']
        read_only_fields = ['id', 'amount','status', 'transaction_type', 'description', 'timestamp', 'reference_id']

class PurchaseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

class ProviderCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderCredit
        fields = ['balance']
        read_only_fields = ['balance']

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'payment_details']
    
    def validate_amount(self, value):
        provider = self.context['request'].user.provider_profile
        provider_credit, created = ProviderCredit.objects.get_or_create(provider=provider)
        
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than 0")
        
        if value > provider_credit.balance:
            raise serializers.ValidationError("Insufficient balance")
        
        return value

class WithdrawalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'status', 'requested_at', 'processed_at']
        read_only_fields = ['id', 'amount', 'status', 'requested_at', 'processed_at']
