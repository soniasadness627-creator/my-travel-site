import psycopg2
import os
import django

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth.hashers import make_password

# Дані для підключення до PostgreSQL на Render
conn = psycopg2.connect(
    host="dpg-d7lu6stckfvc739d1g5g-a.oregon-postgres.render.com",
    port=5432,
    user="tourconstructor_db_user",
    password="cBhJLcMbUBW0GBLbaeR4NnIiexk1nTb9",
    dbname="tourconstructor_db",
    sslmode="require"
)

cur = conn.cursor()

# 1. Подивимось, які є суперадміни
cur.execute("SELECT id, username, email FROM users_user WHERE is_superuser=true;")
admins = cur.fetchall()
print("СУПЕРАДМІНИ:")
for admin in admins:
    print(f"  ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}")

# 2. Оновлюємо пароль для admin
new_password = "admin12345"
hashed_password = make_password(new_password)

cur.execute(
    "UPDATE users_user SET password = %s WHERE username = 'admin';",
    [hashed_password]
)
conn.commit()
print(f"\n✅ Пароль для 'admin' оновлено на '{new_password}'")

# 3. Створюємо AgentSite
cur.execute("""
    INSERT INTO constructor_agentsite 
    (user_id, slug, agency_name, hero_title, hero_subtitle, show_news, show_operator_logos, show_superadmin_tours, created_at, updated_at, primary_color, secondary_color)
    SELECT id, 'admin-site', 'Admin Agency', 'Ваша подорож починається тут', 'Знайдіть ідеальний тур за лічені хвилини', true, false, true, NOW(), NOW(), '#086745', '#02432c'
    FROM users_user WHERE username = 'admin'
    ON CONFLICT (user_id) DO NOTHING;
""")
conn.commit()
print("✅ AgentSite створено або вже існує")

cur.close()
conn.close()
print("\n✅ ГОТОВО! Тепер ви можете увійти в адмінку!")