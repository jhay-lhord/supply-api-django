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

def get_user_role(user):
    """Get the role of the user from their group."""
    if user.is_authenticated:
        roles = user.groups.values_list('name', flat=True)  # Get all group names as a list
        return roles
    return []

def get_user_from_token(request):
    token = request.COOKIES.get("access_token")
    if token:
        try:
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
        logger.info("No JWT token found in cookies.")
    
    return AnonymousUser()

class AuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        logger.debug("Processing request through AuthenticatedUserMiddleware.")
        try:
            user = get_user_from_token(request)
            logger.debug(f"User extracted from token: {user}")
            set_current_user(user)
            request.user = SimpleLazyObject(lambda: user)
            roles = get_user_role(user)
            logger.debug(f"Roles for user {user}: {roles}")
        except Exception as e:
            logger.error(f"Unexpected error in middleware: {e}")
        response = self.get_response(request)
        logger.debug(f'Processed response in AuthenticatedUserMiddleware: {response}')
        return response
