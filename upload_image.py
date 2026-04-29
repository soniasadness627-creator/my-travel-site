import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'djvycubir'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '649993464552661'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'kwwtOaPRA4fv4-_QpL-0sxyRVZ0')
)

# Шлях до вашого фото
image_path = r"C:\Users\Admin\PycharmProjects\DjangoProject1\static\images\alex-turcu-Y-fLrdnQ68Y-unsplash.jpg"

print("🚀 ЗАВАНТАЖЕННЯ ФОТО НА CLOUDINARY...")

try:
    result = cloudinary.uploader.upload(
        image_path,
        folder="landing_images",
        public_id="happy_agent",
        transformation=[
            {'quality': 'auto'},
            {'width': 800, 'height': 800, 'crop': 'limit'}
        ]
    )
    print("\n✅ ФОТО УСПІШНО ЗАВАНТАЖЕНО!")
    print(f"📷 URL: {result['secure_url']}")

    # Зберігаємо URL у файл
    with open('image_url.txt', 'w', encoding='utf-8') as f:
        f.write(result['secure_url'])
    print("\n💾 URL збережено у файл: image_url.txt")

except Exception as e:
    print(f"\n❌ ПОМИЛКА: {e}")