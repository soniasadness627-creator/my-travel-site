from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User


@receiver(post_save, sender=User)
def set_agent_permissions(sender, instance, created, **kwargs):
    if instance.is_agent:
        # Робимо агента персоналом
        if not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=['is_staff'])

        # Список моделей, до яких агент має мати доступ
        models_to_add = ['tour', 'booking', 'priceoption', 'review', 'consultation', 'news', 'city']

        for model_name in models_to_add:
            try:
                content_type = ContentType.objects.get(app_label='tours', model=model_name)
                permissions = Permission.objects.filter(content_type=content_type)
                for perm in permissions:
                    if not instance.user_permissions.filter(id=perm.id).exists():
                        instance.user_permissions.add(perm)
            except ContentType.DoesNotExist:
                pass