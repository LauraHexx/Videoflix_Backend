from django.urls import path
from .views import RegistrationView, LoginView, RegistrationVerifyView, PasswordResetRequestView, PasswordResetConfirmView, LogoutView

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path('registration/verify/<str:token>/',
         RegistrationVerifyView.as_view(), name='verify-email'),
    path("login/", LoginView.as_view(), name="login"),
    path("password-reset/request/", PasswordResetRequestView.as_view(),
         name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(),
         name="password-reset-confirm"),
    path('logout/', LogoutView.as_view(), name='logout'),
]
