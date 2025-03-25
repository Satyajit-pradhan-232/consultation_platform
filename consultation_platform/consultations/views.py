from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Consultation
from .serializers import (
    ConsultationSerializer, ConsultationRequestSerializer,
    ConsultationAcceptRejectSerializer, ConsultationEndSerializer,
     ConsultationHistorySerializer, ConsultationCancelSerializer
)
from providers.models import Provider
from django.db import transaction
from django.utils import timezone
from credits.models import UserCredit, ProviderCredit, Transaction
from channels.layers import get_channel_layer # For sending messages
from asgiref.sync import async_to_sync

class ConsultationRequestView(generics.CreateAPIView):
    serializer_class = ConsultationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user_credit, _ = UserCredit.objects.get_or_create(user=self.request.user)
        #basic check, will refractor later
        if user_credit.balance <= 0:
            return Response({'error': 'Insufficient credits'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

class ConsultationAcceptRejectView(generics.UpdateAPIView):
    serializer_class = ConsultationAcceptRejectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Consultation.objects.all()

    def update(self, request, *args, **kwargs):
        consultation = self.get_object()
        action = self.kwargs.get('action')

        if consultation.provider.user != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        if consultation.status != Consultation.REQUESTED:
             return Response({'error': 'Consultation is not in requested state'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if action == 'accept':
                consultation.status = Consultation.ACCEPTED
                consultation.save()

                # Send message to start chat (via Channels)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"consultation_{consultation.id}", {
                        "type": "consultation.accepted",
                        "consultation_id": consultation.id,
                    }
                )
                print(f"CONSULTATION ACCEPTED (view): {consultation.user.email} - {consultation.provider.user.email}")

            elif action == 'reject':
                consultation.status = Consultation.REJECTED
                consultation.save()
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(ConsultationSerializer(consultation).data)

class ConsultationCancelView(generics.UpdateAPIView):
    serializer_class = ConsultationCancelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Consultation.objects.all()

    def update(self, request, *args, **kwargs):
        consultation = self.get_object()
        
        # Only allow cancellation if the consultation is requested or accepted
        if consultation.status not in [Consultation.REQUESTED, Consultation.ACCEPTED]:
            return Response({'error': 'Consultation cannot be cancelled in its current state'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only the user or provider involved can cancel
        if request.user != consultation.user and request.user != consultation.provider.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            consultation.status = Consultation.CANCELLED
            consultation.save()

             # Send message to cancel chat (via Channels)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"consultation_{consultation.id}", {
                    "type": "consultation.cancelled",
                    "consultation_id": consultation.id,
                }
            )
            print(f"CONSULTATION CANCELED: {consultation.user.email} - {consultation.provider.user.email}")

        return Response(ConsultationSerializer(consultation).data)

class ConsultationEndView(generics.UpdateAPIView):
    serializer_class = ConsultationEndSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Consultation.objects.all()

    def update(self, request, *args, **kwargs):
        # We'll handle this in chat consumer
        consultation = self.get_object()
        
        if consultation.status != Consultation.ONGOING:
            return Response({'error': 'Consultation is not ongoing'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user != consultation.user and request.user != consultation.provider.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Send message to end consultation (via Channels)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"consultation_{consultation.id}", {
                "type": "consultation.end",
                "consultation_id": consultation.id,
            }
        )
        print(f"CONSULTATION END REQUESTED (view): {consultation.user.email} - {consultation.provider.user.email}")
        return Response({'message': 'End consultation request sent.'}, status=status.HTTP_200_OK)


class UserConsultationHistoryView(generics.ListAPIView):
    serializer_class = ConsultationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(user=self.request.user).order_by('-created_at')

class ProviderConsultationHistoryView(generics.ListAPIView):
    serializer_class = ConsultationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        provider = get_object_or_404(Provider, user=self.request.user)
        return Consultation.objects.filter(provider=provider).order_by('-created_at')
    
class ProviderConsultationRequestsView(generics.ListAPIView): 
    serializer_class = ConsultationSerializer  # Use the standard serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        provider = get_object_or_404(Provider, user=self.request.user)
        # Filter for consultations that are in the 'requested' state AND belong to this provider.
        return Consultation.objects.filter(provider=provider, status=Consultation.REQUESTED)