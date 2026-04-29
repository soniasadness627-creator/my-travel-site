import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
import time

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'djvycubir'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '649993464552661'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'kwwtOaPRA4fv4-_QpL-0sxyRVZ0')
)

# ВАШІ 3 ВІДЕО ДЛЯ ЗАВАНТАЖЕННЯ
videos = [
    {
        'path': r"C:\Users\Admin\PycharmProjects\DjangoProject1\static\4010511-hd_1920_1080_25fps.mp4",
        'name': 'hero_video_1'
    },
    {
        'path': r"C:\Users\Admin\PycharmProjects\DjangoProject1\static\11126484-hd_1920_1080_25fps.mp4",
        'name': 'hero_video_2'
    },
    {
        'path': r"C:\Users\Admin\PycharmProjects\DjangoProject1\static\20311697-uhd_3840_2160_30fps.mp4",
        'name': 'hero_video_3'
    },
]

print("🚀 ЗАВАНТАЖЕННЯ 3 ВІДЕО НА CLOUDINARY...")
print("=" * 50)

# Відкриваємо файл для збереження URL
with open('video_urls.txt', 'w', encoding='utf-8') as f:
    f.write("СПИСОК URL ВІДЕО НА CLOUDINARY:\n")
    f.write("=" * 50 + "\n\n")

for video in videos:
    try:
        print(f"\n📹 Завантаження: {video['name']}")

        # Для великого відео (hero_video_3) використовуємо спеціальні параметри
        if video['name'] == 'hero_video_3':
            result = cloudinary.uploader.upload(
                video['path'],
                resource_type="video",
                folder="landing_videos",
                public_id=video['name'],
                timeout=120,  # Збільшуємо таймаут
                transformation=[
                    {'quality': 'auto'},
                    {'width': 1920, 'crop': 'limit'}  # Зменшуємо розмір
                ]
            )
        else:
            result = cloudinary.uploader.upload(
                video['path'],
                resource_type="video",
                folder="landing_videos",
                public_id=video['name'],
                transformation=[
                    {'quality': 'auto'},
                    {'width': 1920, 'crop': 'limit'}
                ]
            )

        url = result['secure_url']
        print(f"   ✅ УСПІШНО!")
        print(f"   🔗 URL: {url}")

        # Зберігаємо URL у файл
        with open('video_urls.txt', 'a', encoding='utf-8') as f:
            f.write(f"{video['name']}:\n")
            f.write(f"{url}\n\n")

    except Exception as e:
        print(f"   ❌ ПОМИЛКА для {video['name']}: {e}")
        print(f"   🔄 Спробуємо альтернативний метод...")

        # Альтернативний метод для великого відео
        try:
            result = cloudinary.uploader.upload(
                video['path'],
                resource_type="video",
                folder="landing_videos",
                public_id=video['name'],
                timeout=180,
                eager=[
                    {'width': 1920, 'height': 1080, 'crop': 'limit', 'quality': 'auto'}
                ],
                eager_async=True
            )

            # Чекаємо трохи для обробки
            time.sleep(5)

            # Отримуємо готовий URL
            url = result['secure_url']
            print(f"   ✅ УСПІШНО (альтернативний метод)!")
            print(f"   🔗 URL: {url}")

            with open('video_urls.txt', 'a', encoding='utf-8') as f:
                f.write(f"{video['name']}:\n")
                f.write(f"{url}\n\n")
        except Exception as e2:
            print(f"   ❌ ДРУГА СПРОБА ТАКОЖ НЕВДАЛА: {e2}")

print("\n" + "=" * 50)
print("✅ ГОТОВО!")
print("📄 URL збережено у файл: video_urls.txt")