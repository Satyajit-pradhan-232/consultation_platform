from django.urls import path
from .views import (
    ConsultationRequestView, ConsultationAcceptRejectView,
    ConsultationEndView, ProviderConsultationRequestsView, UserConsultationHistoryView,
    ProviderConsultationHistoryView, ConsultationCancelView
)

urlpatterns = [
    path('request/', ConsultationRequestView.as_view(), name='consultation-request'),
    path('requests/provider/me/', ProviderConsultationRequestsView.as_view(), name='provider-consultation-requests'),
    path('<int:pk>/cancel/', ConsultationCancelView.as_view(), name='consultation-cancel'),
    path('<int:pk>/end/', ConsultationEndView.as_view(), name='consultation-end'),
    path('<int:pk>/<str:action>/', ConsultationAcceptRejectView.as_view(), name='consultation-accept-reject'),
    path('me/', UserConsultationHistoryView.as_view(), name='user-consultation-history'),
    path('provider/me/', ProviderConsultationHistoryView.as_view(), name='provider-consultation-history'),
]