from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює суперадміна, якщо його ще немає'

    def handle(self, *args, **options):
        # Створюємо або оновлюємо суперадміна Artur
        user, created = User.objects.get_or_create(
            username='Artur',
            defaults={
                'email': 'artur@example.com',
                'is_superuser': True,
                'is_staff': True
            }
        )

        # Встановлюємо пароль
        user.set_password('ваш_пароль')  # ← ЗАМІНІТЬ на пароль, який ви хочете
        user.is_superuser = True
        user.is_staff = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Суперадмін "{user.username}" створений!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Суперадмін "{user.username}" оновлений!'))

        self.stdout.write(self.style.SUCCESS(f'Логін: Artur'))
        self.stdout.write(self.style.SUCCESS(f'Пароль: (встановлений вами)'))