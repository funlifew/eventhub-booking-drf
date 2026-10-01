from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .models import User

def get_user_by_login(login):
    login = login.strip()

    return (
        User.objects
        .filter(
            Q(username__iexact=login)
            | Q(email__iexact=login)
        )
        .first()
    )

def get_user_by_email(email):
    return (
        User.objects
        .filter(email__iexact=email.strip())
        .first()
    )

def get_user_from_uid(uidb64):
    try:
        decoded_uid = force_str(
            urlsafe_base64_decode(uidb64)
        )
        
        user_id = User._meta.pk.to_python(
            decoded_uid
        )
        
        return User.objects.filter(
            pk=user_id,
        ).first()
    
    except (
        TypeError,
        ValueError,
        OverflowError,
        ValidationError,
    ):
        return None