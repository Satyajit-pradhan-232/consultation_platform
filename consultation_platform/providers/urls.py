from django.urls import path
from .views import (
    ProviderRegistrationView,
    ProviderProfileView,
    ProviderListView,
    ProviderDetailView,
    ProviderLoginView,
    ProviderAverageRatingView,
)

urlpatterns = [
    path('register/', ProviderRegistrationView.as_view(), name='provider-register'),
    path('login/', ProviderLoginView.as_view(), name='provider-login'),
    path('me/', ProviderProfileView.as_view(), name='provider-profile'),
    path('me/average-rating/', ProviderAverageRatingView.as_view(), name='provider-average-rating'),
    path('', ProviderListView.as_view(), name='provider-list'),
    path('<int:pk>/', ProviderDetailView.as_view(), name='provider-detail'),
]