from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from .serializers import RegistrationSerializer, LoginSerializer, UserVerifiedSerializer
from ..models import CustomUser


class RegistrationView(APIView):
    """Handle user registration and return token and user info."""

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles user registration by validating and saving the input data.
        If the data is valid, a new user is created and an authentication token 
        is returned. Otherwise, validation errors are returned.
        """
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            return Response({
                "token": token.key,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


######### todo#########
class RegistrationVerifyView(APIView):
    """
    Verifies the email token and activates the user's email.
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user = CustomUser.objects.get(verification_token=token)
            user.is_verified = True
            user.verification_token = ""
            user.save()
            # Nach erfolgreicher Verifikation weiterleiten
            frontend_login_url = getattr(
                settings, "FRONTEND_URL", "http://localhost:4200") + "/login"
            return redirect(frontend_login_url)
        except CustomUser.DoesNotExist:
            return HttpResponse("Ungültiger oder abgelaufener Verifizierungslink.", status=400)


####################


class UserVerified(APIView):
    """
    Checks if a verified user with this email already exists.
    If so, signup is not allowed (already registered & verified).
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Checks if a user with the given email is already verified.
        Validates the input and returns a boolean indicating whether the user
        has already completed email verification.
        """
        serializer = UserVerifiedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        already_verified = CustomUser.objects.filter(
            email=email, is_verified=True
        ).exists()

        return Response({"userIsAlreadyVerified": already_verified}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """Authenticates a verified user using email and returns an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles user login by validating credentials and authentication.
        Returns a token if credentials are valid and the user is verified.
        For any failure (invalid data, wrong password, unverified account), 
        a generic error message is returned to prevent user enumeration.
        """
        serializer = self._validate_serializer(request)
        if not serializer:

            return self._invalid_credentials_response()

        user = self._authenticate_user(serializer)
        if not user or not user.is_verified:

            return self._invalid_credentials_response()

        return self._success_response(user)

    def _validate_serializer(self, request):
        """Validates the login serializer with request data."""
        self.serializer = LoginSerializer(data=request.data)
        if self.serializer.is_valid():
            return self.serializer
        return None

    def _authenticate_user(self, serializer):
        """Authenticates user using provided email and password."""
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        return authenticate(email=email, password=password)

    def _invalid_credentials_response(self):
        """Returns generic error response for any login failure."""
        return Response(
            {"error": "Invalid login credentials."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _success_response(self, user):
        """Returns success response with auth token and user data."""
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_200_OK)
