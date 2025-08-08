from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User

@receiver(post_save, sender=User)
def user_moderation_notification(sender, instance, created, **kwargs):
    """
    Notify moderator when a non-buyer registers (pending status) via chosen methods.
    """
    if created and instance.account_status == 'pending':
        methods = instance.moderator_notification_methods or []
        subject = f"New user pending: {instance.email}"
        message = f"User {instance.full_name} ({instance.account_type}) awaits moderation."
        recipient_list = ['moderator@example.com']  # replace with real moderator emails
        if 'email' in methods:
            send_mail(subject, message, None, recipient_list)