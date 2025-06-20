from django.contrib.auth.backends import ModelBackend
from django.core.mail.backends.smtp import EmailBackend
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


class UnsafeTLSBackend(EmailBackend):
    """
    Custom SMTP backend that disables SSL certificate verification for STARTTLS.
    """

    def open(self):
        """
        Open a network connection with SSL verification disabled.
        """
        if self.connection:
            return False
        try:
            self.connection = self._create_smtp_connection()
            self._start_tls_if_needed()
            self._login_if_needed()
            return True
        except Exception:
            if self.fail_silently:
                return False
            raise

    def _create_smtp_connection(self):
        """
        Create and return an SMTP connection.
        """
        import smtplib
        return smtplib.SMTP(
            self.host,
            self.port,
            timeout=self.timeout,
        )

    def _start_tls_if_needed(self):
        """
        Start TLS with SSL verification disabled if required.
        """
        if self.use_tls:
            import ssl
            context = ssl._create_unverified_context()
            self.connection.starttls(context=context)

    def _login_if_needed(self):
        """
        Log in to the SMTP server if credentials are provided.
        """
        if self.username and self.password:
            self.connection.login(self.username, self.password)
