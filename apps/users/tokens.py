from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(
    PasswordResetTokenGenerator,
):
    key_salt = (
        'apps.users.tokens',
        'AccountActivationTokenGenerator'
    )
    
    def _make_hash_value(
        self,
        user,
        timestamp,
    ):
        verified_at = (
            user.email_verified_at.isoformat()
            if user.email_verified_at
            else ""
        )
        
        return (
            f"{user.pk}"
            f"{user.password}"
            f"{timestamp}"
            f"{user.email}"
            f"{user.is_active}"
            f"{verified_at}"
        )

account_activation_token = (
    AccountActivationTokenGenerator()
)