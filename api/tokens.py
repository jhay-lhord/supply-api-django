import jwt
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


class CustomRefreshToken(RefreshToken):

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token['email'] = user.email  # Add the email to the token payload
        return token


def get_tokens_for_user(user):
    refresh = CustomRefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def token_decoder(token):

    try:
        # Decode the token
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        print(f'decoded data = {decoded_data}')
        return decoded_data['user_id']  # Assuming 'user_id' is part of the token payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid
        return None
