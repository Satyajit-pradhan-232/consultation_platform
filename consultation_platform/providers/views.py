from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Provider
from users.models import User
from .serializers import ProviderRegisstrationSerializer, ProviderProfileSerializer, ProviderListSerializer, ProviderDetailSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

class ProviderRegistrationView(generics.CreateAPIView):
    serializer_class = ProviderRegisstrationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Provider.objects.all()

class ProviderLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = User.objects.filter(email=email).first()

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({'error': 'Invalid password'}, status=status.HTTP_404_NOT_FOUND)

        provider = Provider.objects.filter(user=user).first()

        if provider is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class ProviderProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Provider, user=self.request.user)
    
class ProviderListView(generics.ListAPIView):
    serializer_class = ProviderListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Provider.objects.filter(is_verified=True)

    def get_queryset(self):
        queryset = super().get_queryset()
        specialty = self.request.query_params.get('specialty', None)
        if specialty:
            queryset = queryset.filter(specialty=specialty)
        return queryset
    
class ProviderDetailView(generics.RetrieveAPIView):
    serializer_class = ProviderDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Provider.objects.filter(is_verified=True)

class ProviderAverageRatingView(generics.GenericAPIView):
    serializer_class = ProviderProfileSerializer 

    def get(self, request, *args, **kwargs):
        provider = get_object_or_404(Provider, user=self.request.user)
        return Response({"average_rating": provider.average_rating}, status = status.HTTP_200_OK)
    


