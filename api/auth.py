import logging
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')
        print(f"Token: {token}")

        if not token:
            return None  # No token found, skip this authentication class

        try:
            validated_token = self.get_validated_token(token)

        except AuthenticationFailed as e:
            logger.warning(f"Token Validation Failed {str(e)}")
            raise AuthenticationFailed(f"Token Validation Failed {str(e)}")
          
        try:
            user = self.get_user(validated_token) 
            return user, validated_token
        except Exception as e:
            logger.error(f"Error retrieving User: {str(e)}")
            raise AuthenticationFailed(f"Error retrieving User: {str(e)}")
