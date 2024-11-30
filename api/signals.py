from django.db.models.signals import post_save, post_delete
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .utils import get_current_user
from .middleware import get_user_role
from .models import RecentActivity
import logging

logger = logging.getLogger(__name__)

def create_update_activity(sender, instance, created, **kwargs):
    user = get_current_user()
    user_role = get_user_role(user)
    logger.info(f"create_update_activity signal triggered for {sender.__name__}. User: {user}")
    activity_type = 'Added' if created else 'Updated'
    content_type = ContentType.objects.get_for_model(instance)
    
    if user:  
        RecentActivity.objects.create(  
            user=user,
            user_role= user_role,
            activity_type=activity_type,
            content_type=content_type,
            object_id=instance.pk,
        )
        logger.info(f"RecentActivity created for {activity_type} action by {user}")
    else:
        logger.warning(f"No user found for {sender.__name__} {activity_type} action")

def delete_activity(sender, instance, **kwargs):
    user = get_current_user()
    user_role = get_user_role()

    logger.info(f"delete_activity signal triggered for {sender.__name__}. User: {user}")

    content_type = ContentType.objects.get_for_model(instance)
    
    if user:
        RecentActivity.objects.create(
            user=user,
            user_role=user_role,
            activity_type='Deleted',
            content_type=content_type,
            object_id=instance.pk,
        )
        logger.info(f"RecentActivity created for DELETE action by {user}")
    else:
        logger.warning(f"No user found for {sender.__name__} DELETE action")

# List of model names you want to track
models_to_track = ['PurchaseRequest', 'Item', 'RequestForQoutation', 'AbstractOfQoutation']

for model_name in models_to_track:
    model = apps.get_model('api', model_name)
    post_save.connect(create_update_activity, sender=model)
    post_delete.connect(delete_activity, sender=model)