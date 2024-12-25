import logging
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

logger = logging.getLogger(__name__)

def is_token_blacklisted(token):
    return BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()



class CookieJWTAuthentication(JWTAuthentication):
    
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')
        
        if not token:
            return None  # No token found, skip this authentication class

        try:
            validated_token = self.get_validated_token(token)
           
            if is_token_blacklisted(validated_token):
                print("Token is blacklisted")
                raise AuthenticationFailed("Token is blacklisted")
            
            user_id = validated_token.get("user_id")
            
            if not user_id:
                raise AuthenticationFailed("Invalid token: user_id not found")
            
            user = self.get_user(validated_token)  # This should work with a validated token
            
            return (user, validated_token)
        except AuthenticationFailed as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise AuthenticationFailed(f"Token validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            raise AuthenticationFailed(f"Error retrieving user: {str(e)}")
