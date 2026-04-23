from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User
from tours.models import Tour


@receiver(post_save, sender=User)
def set_agent_permissions(sender, instance, created, **kwargs):
    """
    Автоматично надає агентам права доступу до адмін-панелі (is_staff=True)
    та всі права на модель Tour (add, change, delete, view).
    """
    if instance.is_agent:
        # Робимо агента персоналом (is_staff)
        if not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=['is_staff'])

        # Надаємо всі права на модель Tour
        content_type = ContentType.objects.get_for_model(Tour)
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            if not instance.user_permissions.filter(id=perm.id).exists():
                instance.user_permissions.add(perm)