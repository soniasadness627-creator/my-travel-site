from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює суперадміна при першому запуску'

    def handle(self, *args, **options):
        # Видаляємо старого користувача, якщо він є
        User.objects.filter(username='admin').delete()

        # Створюємо нового суперадміна
        User.objects.create_superuser(
            username='admin',
            email='admin@clubdatour.com.ua',
            password='admin12345'
        )

        self.stdout.write(self.style.SUCCESS('=' * 40))
        self.stdout.write(self.style.SUCCESS('СУПЕРАДМІН СТВОРЕНИЙ!'))
        self.stdout.write(self.style.SUCCESS('Логін: admin'))
        self.stdout.write(self.style.SUCCESS('Пароль: admin12345'))
        self.stdout.write(self.style.SUCCESS('=' * 40))