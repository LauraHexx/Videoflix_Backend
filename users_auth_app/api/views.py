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


class UserVerified(APIView):
    """
    Checks if a verified user with this email already exists.
    If so, signup is not allowed (already registered & verified).
    permission_classes = [AllowAny]
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserVerifiedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        already_verified = CustomUser.objects.filter(
            email=email, is_verified=True
        ).exists()

        return Response({"userIsAlreadyVerified": already_verified}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """
    Verifies the email token and activates the user's email.
    """

    def get(self, request, token):
        try:
            user = CustomUser.objects.get(verification_token=token)
            user.is_email_verified = True  # falls du so ein Feld hast
            user.verification_token = ""
            user.save()
            # Nach erfolgreicher Verifikation weiterleiten
            frontend_login_url = getattr(
                settings, "FRONTEND_URL", "http://localhost:4200") + "/login"
            return redirect(frontend_login_url)
        except CustomUser.DoesNotExist:
            return HttpResponse("Ungültiger oder abgelaufener Verifizierungslink.", status=400)


class LoginView(APIView):
    """Authenticate user using email and return auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(email=email, password=password)
            if user is not None:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "email": user.email,
                    "user_id": user.id
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticates a verified user using email and returns an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles user login by validating credentials and checking email verification.

        Returns a token if credentials are valid and the user is verified.
        Otherwise, returns an appropriate error message.
        """
        serializer = self._validate_serializer(request)
        if not serializer:
            return self._invalid_serializer_response()

        user = self._authenticate_user(serializer)
        if not user:
            return self._invalid_credentials_response()

        if not user.is_verified:
            return self._unverified_user_response()

        return self._success_response(user)

    def _validate_serializer(self, request):
        """Validates the login serializer with request data."""
        self.serializer = LoginSerializer(data=request.data)
        if self.serializer.is_valid():
            return self.serializer
        return None

    def _invalid_serializer_response(self):
        """Returns error response if serializer validation fails."""
        return Response(self.serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _authenticate_user(self, serializer):
        """Authenticates user using provided email and password."""
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        return authenticate(email=email, password=password)

    def _invalid_credentials_response(self):
        """Returns error response for invalid credentials."""
        return Response(
            {"error": "Invalid login credentials."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _unverified_user_response(self):
        """Returns error response if user email is not verified."""
        return Response(
            {"error": "Email address has not been verified."},
            status=status.HTTP_403_FORBIDDEN
        )

    def _success_response(self, user):
        """Returns success response with auth token and user data."""
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_200_OK)
