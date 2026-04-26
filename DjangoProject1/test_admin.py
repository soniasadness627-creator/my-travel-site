import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

print("=" * 50)
print("ДІАГНОСТИКА СУПЕРАДМІНА")
print("=" * 50)

# Перевіряємо, чи є користувач admin
try:
    user = User.objects.get(username='admin')
    print(f"✓ Користувач 'admin' існує")
    print(f"  - is_active: {user.is_active}")
    print(f"  - is_superuser: {user.is_superuser}")
    print(f"  - is_staff: {user.is_staff}")

    # Перевіряємо пароль
    auth_user = authenticate(username='admin', password='admin12345')
    if auth_user:
        print(f"✓ Пароль 'admin12345' вірний!")
    else:
        print(f"✗ Пароль 'admin12345' НЕВІРНИЙ!")

        # Спробуємо скинути пароль ще раз
        user.set_password('admin12345')
        user.save()
        print(f"  Пароль скинуто повторно!")

except User.DoesNotExist:
    print(f"✗ Користувач 'admin' НЕ ІСНУЄ!")
    User.objects.create_superuser(
        username='admin',
        email='admin@clubdatour.com.ua',
        password='admin12345'
    )
    print(f"✓ Суперадмін створений!")

print("=" * 50)