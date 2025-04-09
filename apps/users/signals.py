from .models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from services.email_service import EmailService

@receiver(post_save, sender=User, dispatch_uid="user_welcome_email")
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        email_service = EmailService()
        user_full_name = f"{instance.name} {instance.family_name}"
        email_service.send_email(
            recipient_email=instance.email,
            template_type='welcome',
            name=user_full_name
        )
        