from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .utils import get_current_user
from .middleware import get_user_role
from .models import RecentActivity, TrackStatus, PurchaseRequest
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
    user_role = get_user_role(user)

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

# List of model names to include in the recent activity
models_to_track = ['PurchaseRequest', 'Item', 'RequestForQoutation', 'AbstractOfQuotation']

for model_name in models_to_track:
    model = apps.get_model('api', model_name)
    post_save.connect(create_update_activity, sender=model)
    post_delete.connect(delete_activity, sender=model)
    
@receiver(post_save, sender=PurchaseRequest)
def update_status_on_save(sender, instance, **kwargs):
    # Get the dynamic description based on the status
    description = instance.get_status_description()
    
    # Check if the status has changed
    # Check if the most recent status for this PR No is the same as the current status
    latest_status = TrackStatus.objects.filter(pr_no=instance).order_by('-updated_at').first()
    
    if latest_status and latest_status.status == instance.status:
        print("Status is the same as the latest. Skipping duplicate status entry.")
        return  # Don't create a duplicate if the status hasn't changed
    
    
    # Update or create the corresponding Status object
    TrackStatus.objects.create(
        pr_no=instance,  # Link to the PurchaseRequest
        status=instance.status,
        description=description,
    )

