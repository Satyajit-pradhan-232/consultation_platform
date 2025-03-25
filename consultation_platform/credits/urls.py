from django.urls import path
from .views import (
    CreditPurchaseView, 
    PaymentWebhookView,
    UserCreditBalanceView,
    UserTransactionHistoryView,
    ProviderCreditBalanceView,
    WithdrawalRequestView,
    WithdrawalHistoryView
)

urlpatterns = [
    path('purchase/', CreditPurchaseView.as_view(), name='purchase-credits'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('me/', UserCreditBalanceView.as_view(), name='user-credit-balance'),
    path('transactions/', UserTransactionHistoryView.as_view(), name='user-transactions'),
    path('providers/me/', ProviderCreditBalanceView.as_view(), name='provider-credit-balance'),
    path('providers/me/withdraw/', WithdrawalRequestView.as_view(), name='provider-withdrawal-request'),
    path('providers/me/withdrawals/', WithdrawalHistoryView.as_view(), name='provider-withdrawal-history'),
]
