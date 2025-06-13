from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class VerifiedEmailBackend(ModelBackend):
    """
    Custom backend to authenticate users by email, password, and verified status.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate user by email and password only if user is verified.

        Returns the user if authentication succeeds, else None.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None

        if not user.is_verified:
            return None

        return user
