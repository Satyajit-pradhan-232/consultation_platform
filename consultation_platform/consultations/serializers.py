from rest_framework import serializers
from providers.models import Provider
from .models import Consultation
from users.serializers import UserProfileSerializer
from providers.serializers import ProviderDetailSerializer, ProviderListSerializer

class ConsultationSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    provider = ProviderListSerializer(read_only=True)
    class Meta:
        model = Consultation
        # fields = ['id', 'user', 'provider', 'status', 'start_time', 'end_time', 'created_at']
        fields = '__all__'
        read_only_fields = ['id', 'user', 'provider', 'status', 'start_time', 'end_time', 'created_at']

class ConsultationRequestSerializer(serializers.ModelSerializer):
    provider_id = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all(), write_only=True)
    user = UserProfileSerializer(read_only=True)
    provider = ProviderDetailSerializer(read_only=True)
    class Meta:
        model = Consultation
        fields = ['provider_id', 'user', 'provider', 'id', 'status', 'created_at'] # Include id and status!
        read_only_fields = ['id', 'status', 'user', 'provider', 'created_at'] # Mark as read-only

    def create(self, validated_data):
        user = self.context['request'].user
        provider = validated_data['provider_id']
        consultation = Consultation.objects.create(user=user, provider=provider)
        return consultation

class ConsultationAcceptRejectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = []

class ConsultationEndSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = []

class ConsultationCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = []
        
class ConsultationHistorySerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    provider = ProviderListSerializer(read_only=True)
    class Meta:
        model = Consultation
        # fields = ['id', 'user', 'provider', 'status', 'start_time', 'end_time', 'created_at']
        fields = '__all__'
        read_only_fields = ['id', 'user', 'provider', 'status', 'start_time', 'end_time', 'created_at']



