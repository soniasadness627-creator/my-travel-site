from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює суперадміна або скидає пароль'

    def handle(self, *args, **options):
        # Знаходимо суперадміна або створюємо
        user, created = User.objects.get_or_create(
            username='So',
            defaults={
                'email': 'so@example.com',
                'is_superuser': True,
                'is_staff': True
            }
        )

        # Скидаємо пароль
        user.set_password('So12345')
        user.is_superuser = True
        user.is_staff = True
        user.save()

        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS(f'Суперадмін "{user.username}" оновлений!'))
        self.stdout.write(self.style.SUCCESS('Логін: So'))
        self.stdout.write(self.style.SUCCESS('Пароль: So12345'))
        self.stdout.write("=" * 50)