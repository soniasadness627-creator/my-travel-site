from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Створює суперадміна, якщо його ще немає'

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='So',
                email='so@example.com',
                password='So12345'
            )
            self.stdout.write(self.style.SUCCESS('Суперадмін створений!'))
        else:
            self.stdout.write(self.style.WARNING('Суперадмін вже існує'))