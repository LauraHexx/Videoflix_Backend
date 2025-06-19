from rest_framework import serializers
from ..models import CustomUser
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password


class RegistrationSerializer(serializers.ModelSerializer):
    """Register or update unverified user."""

    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(validators=[])

    class Meta:
        model = CustomUser
        fields = ("email", "password", "repeated_password")

    def validate(self, data):
        """Ensure passwords match."""
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]

        user = CustomUser.objects.filter(email=email).first()
        if user:
            if user.is_verified:
                raise serializers.ValidationError({
                    "email": ["User with this email already exists."]
                })
            user = self._update_unverified_user(user, password)
            created = False
        else:
            user = self._create_new_user(validated_data)
            created = True

        return user, created

    def _update_unverified_user(self, user, password):
        """Update unverified user password and mark verified."""
        user.password = make_password(password)
        user.save(update_fields=["password", "is_verified"])
        Token.objects.get_or_create(user=user)
        return user

    def _create_new_user(self, validated_data):
        """Create new user and token."""
        validated_data.pop("repeated_password")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            username=None
        )
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
