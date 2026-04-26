from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює суперадміна, якщо його ще немає'

    def handle(self, *args, **options):
        # ВИВЕСТИ ВСІХ КОРИСТУВАЧІВ
        self.stdout.write("=" * 50)
        self.stdout.write("=== ВСІ КОРИСТУВАЧІ В БАЗІ ДАНИХ ===")
        users = User.objects.all()
        self.stdout.write(f"ВСЬОГО КОРИСТУВАЧІВ: {users.count()}")

        for user in users:
            self.stdout.write(
                f"Логін: '{user.username}', superuser: {user.is_superuser}, staff: {user.is_staff}, agent: {user.is_agent}")

        self.stdout.write("=" * 50)

        # Шукаємо суперадміна
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            self.stdout.write(self.style.WARNING(f'Суперадмін вже існує: {superusers.first().username}'))
        else:
            # Створюємо нового
            User.objects.create_superuser(
                username='So',
                email='so@example.com',
                password='So12345'
            )
            self.stdout.write(self.style.SUCCESS('Суперадмін створений! (Логін: So, Пароль: So12345)'))