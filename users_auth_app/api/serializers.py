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
        """
        Ensures that both password fields match.
        Raises ValidationError if passwords do not match.
        """
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """
        Creates and returns a new user after removing repeated_password.
        If no username is provided, sets it to None. Also creates an auth token for the user.
        """
        validated_data.pop('repeated_password')
        if 'username' not in validated_data:
            validated_data['username'] = None
        user = CustomUser.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user


class UserVerifiedSerializer(serializers.Serializer):
    """Serializer for verifying if a user with given email is verified."""
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    """Validate login credentials (email and password)."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True)
    password_confirmed = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["password_confirmed"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data
