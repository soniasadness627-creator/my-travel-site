from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Підвищує агента до суперадміна'

    def handle(self, *args, **options):
        # Знайдіть користувача Sonia (або іншого) в базі Render
        user = User.objects.filter(username='Sonia').first()

        if user:
            user.is_superuser = True
            user.is_staff = True
            user.set_password('новий_пароль')  # ← встановіть новий пароль
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Користувача "{user.username}" підвищено до суперадміна!'))
            self.stdout.write(self.style.SUCCESS(f'Логін: {user.username}'))
            self.stdout.write(self.style.SUCCESS(f'Пароль: (встановлений вами)'))
        else:
            self.stdout.write(self.style.WARNING('Користувача Sonia не знайдено'))