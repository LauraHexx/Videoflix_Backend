from rest_framework import serializers
from ..models import CustomUser
from rest_framework.authtoken.models import Token


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new user with email and password."""
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("email", "password", "repeated_password")

    def validate(self, data):
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        # Setze username auf None, falls nicht gesetzt
        if 'username' not in validated_data:
            validated_data['username'] = None
        user = CustomUser.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user
