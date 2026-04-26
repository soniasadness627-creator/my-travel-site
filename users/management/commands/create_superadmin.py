from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює або оновлює суперадміна'

    def handle(self, *args, **options):
        # Шукаємо користувача Sonia
        user = User.objects.filter(username='Sonia').first()

        if user:
            # Якщо знайшли - підвищуємо до суперадміна та скидаємо пароль
            user.is_superuser = True
            user.is_staff = True
            user.set_password('Sonia12345')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Користувача "{user.username}" підвищено до суперадміна!'))
            self.stdout.write(self.style.SUCCESS(f'Логін: {user.username}'))
            self.stdout.write(self.style.SUCCESS(f'Пароль: Sonia12345'))
        else:
            # Якщо не знайшли - створюємо нового суперадміна
            User.objects.create_superuser(
                username='Sonia',
                email='sonia@example.com',
                password='Sonia12345'
            )
            self.stdout.write(self.style.SUCCESS('Суперадміна Sonia створено!'))
            self.stdout.write(self.style.SUCCESS('Логін: Sonia'))
            self.stdout.write(self.style.SUCCESS('Пароль: Sonia12345'))