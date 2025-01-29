from .models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail

@receiver(post_save, sender=User, dispatch_uid="user_welcome_email")
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        print(f"Welcome email sent to {instance.email}")
        send_mail(
            "welcome to naia",
            f"welcome to naia {instance.name} {instance.family_name}",
            "admin@django.com",
            [instance.email],
            fail_silently=False,
        )
