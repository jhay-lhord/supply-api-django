import jwt
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from .utils import set_current_user, get_current_user

logger = logging.getLogger(__name__)

User = get_user_model()

def get_user_from_token(request):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]  # Extract the token
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")
            logger.info(f"Decoded user_id: {user_id} from token")
            
            if user_id:
                user = User.objects.get(id=user_id)
                logger.info(f"Authenticated user: {user}")
                return user
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired.")
        except jwt.DecodeError:
            logger.error("Failed to decode JWT token.")
        except User.DoesNotExist:
            logger.warning(f"User with ID {user_id} does not exist.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
    else:
        logger.info("No Authorization header found in request.")
    
    return AnonymousUser()

class AuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug("Processing request through AuthenticatedUserMiddleware.")
        user = get_user_from_token(request)
        set_current_user(user)
        request.user = SimpleLazyObject(lambda: user)
        response = self.get_response(request)
        logger.debug(f'Processed response in AuthenticatedUserMiddleware. {response}')
        return response
