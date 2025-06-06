from django.urls import path
from .views import RegistrationView, LoginView, VerifyEmailView, UserVerified

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path('registration/verify/<str:token>/',
         VerifyEmailView.as_view(), name='verify-email'),
    path("user-verified/", UserVerified.as_view(), name="user-verified"),
    path("login/", LoginView.as_view(), name="login"),
]
