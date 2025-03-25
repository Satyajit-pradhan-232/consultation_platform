from rest_framework import serializers
from .models import Provider
from users.serializers import UserRegistrationSerializer, UserProfileSerializer
from users.models import User

class ProviderRegisstrationSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()
    specialty = serializers.CharField(required=True)
    rate_per_minute = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    class Meta:
        model = Provider
        fields = ('user', 'specialty', 'rate_per_minute')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data.pop('password2', None)
        user = User.objects.create_user(**user_data)
        user.is_provider=True
        user.save()
        provider = Provider.objects.create(user=user, **validated_data)
        return provider


class ProviderProfileSerializer(serializers.ModelSerializer):
    user =  UserProfileSerializer(read_only=True)
    availability = serializers.JSONField(required=False)
    class Meta:
        model = Provider
        fields = ('id', 'user', 'specialty', 'rate_per_minute', 'availability', 'is_verified', 'average_rating')
        read_only_fields = ('id', 'user', 'is_verified', 'average_rating') 


class ProviderListSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = Provider
        fields = ('id', 'user', 'specialty', 'rate_per_minute', 'average_rating')


class ProviderDetailSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = Provider
        fields = ('id', 'user', 'specialty', 'rate_per_minute', 'availability', 'is_verified', 'average_rating')
