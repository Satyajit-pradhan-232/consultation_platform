from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from .models import UserCredit, ProviderCredit, Transaction, Withdrawal
from .serializers import (
    UserCreditSerializer, TransactionSerializer, PurchaseSerializer,
    ProviderCreditSerializer, WithdrawalRequestSerializer, WithdrawalHistorySerializer
)
from providers.models import Provider
import uuid

# Payment gateway mock
def process_payment(amount):
    # In a real-world scenario, this would communicate with a payment gateway
    # and return a payment session or redirect URL
    return {
        'payment_id': str(uuid.uuid4()),
        'redirect_url': f"paymentGatewayUrl/amount={amount}",
        'status': 'pending'
    }

class CreditPurchaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PurchaseSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            
            
            # Create a transaction with QUEUED status initially
            transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type=Transaction.PURCHASE,
                status=Transaction.QUEUED,
                description=f"Credit purchase of {amount}",
                #reference_id=payment_data['payment_id']
            )

            # Simulate payment gateway integration
            payment_data = process_payment(amount)

            # Update status to PROCESSING once sent to payment gateway
            transaction.status = Transaction.PENDING
            transaction.reference_id = payment_data['payment_id']
            transaction.description = f"Credit purchase of {amount} - Processing"
            transaction.save()
            
            return Response({
                'transaction_id': transaction.id,
                'payment_id': payment_data['payment_id'],
                'redirect_url': payment_data['redirect_url'],
                'status': transaction.status
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]  # Webhooks usually don't require authentication
    
    @transaction.atomic
    def post(self, request):
        # In a real-world scenario, you would verify the webhook signature
        # to ensure it's coming from your payment provider
        
        payment_id = request.data.get('payment_id')
        payment_status = request.data.get('status')
        
        if not payment_id or not payment_status:
            return Response({'error': 'Invalid webhook data'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the transaction by payment_id
        transaction_obj = get_object_or_404(Transaction, reference_id=payment_id)
        
        if payment_status == 'completed':
            # Update user's credit balance
            user_credit, created = UserCredit.objects.get_or_create(user=transaction_obj.user)
            user_credit.balance += transaction_obj.amount
            user_credit.save()
            
            # Update transaction status and description
            transaction_obj.status = Transaction.SUCCESS
            transaction_obj.description = f"Credit purchase of {transaction_obj.amount} - Completed"
            transaction_obj.save()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        elif payment_status == 'failed':
            # Update transaction status and description
            transaction_obj.status = Transaction.FAILED
            transaction_obj.description = f"Credit purchase of {transaction_obj.amount} - Failed"
            transaction_obj.save()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid payment status'}, status=status.HTTP_400_BAD_REQUEST)

class UserCreditBalanceView(generics.RetrieveAPIView):
    serializer_class = UserCreditSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_credit, created = UserCredit.objects.get_or_create(user=self.request.user)
        return user_credit

class UserTransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-timestamp')

class ProviderCreditBalanceView(generics.RetrieveAPIView):
    serializer_class = ProviderCreditSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        provider = get_object_or_404(Provider, user=self.request.user)
        provider_credit, created = ProviderCredit.objects.get_or_create(provider=provider)
        return provider_credit

class WithdrawalRequestView(generics.CreateAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        provider = get_object_or_404(Provider, user=self.request.user)
        withdrawal = serializer.save(provider=provider, status=Withdrawal.PENDING)
        
        # We don't deduct the balance until the withdrawal is approved
        return withdrawal

class WithdrawalHistoryView(generics.ListAPIView):
    serializer_class = WithdrawalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        provider = get_object_or_404(Provider, user=self.request.user)
        return Withdrawal.objects.filter(provider=provider).order_by('-requested_at')
