from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
import logging

# Намагаємося імпортувати Telegram notifier, якщо він налаштований
try:
    from tours.telegram_notifier import send_contact_notification

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Telegram notifier not available. Install it to enable notifications.")

logger = logging.getLogger(__name__)


def index(request):
    """Головна сторінка лендингу"""
    return render(request, 'landing/index.html')


def privacy_policy(request):
    """Сторінка політики конфіденційності для лендингу"""
    return render(request, 'landing/privacy_policy.html')


def terms_of_service(request):
    """Сторінка правил надання послуг для лендингу"""
    return render(request, 'landing/terms_of_service.html')


@csrf_exempt
@require_http_methods(["POST"])
def landing_contact_ajax(request):
    """
    Обробник AJAX запитів з форми лендінгу
    Приймає дані з форми та відправляє сповіщення в Telegram
    """
    try:
        # Отримуємо дані з POST запиту
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                data = request.POST.dict()
        else:
            data = request.POST.dict()

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        agency = data.get('agency', '').strip()
        message = data.get('message', '').strip()

        # Валідація обов'язкових полів
        if not name:
            return JsonResponse({
                'success': False,
                'error': "Введіть ваше ім'я"
            }, status=400)

        if not phone:
            return JsonResponse({
                'success': False,
                'error': "Введіть номер телефону"
            }, status=400)

        # Відправляємо Telegram сповіщення (якщо доступно)
        telegram_sent = False
        if TELEGRAM_AVAILABLE:
            try:
                telegram_sent = send_contact_notification(name, phone, agency, message)
                if telegram_sent:
                    logger.info(f"✅ Telegram notification sent for {name}")
                else:
                    logger.warning(f"⚠️ Telegram notification failed for {name}")
            except Exception as e:
                logger.error(f"❌ Error sending Telegram notification: {e}")
        else:
            logger.warning("⚠️ Telegram notifier not configured, skipping notification")

        # Логуємо отриману заявку
        logger.info(
            f"📋 New contact form submission: Name={name}, Phone={phone}, Agency={agency or 'Not specified'}, Message={message[:50] if message else 'Empty'}, Telegram sent={telegram_sent}")

        # Повертаємо успішну відповідь
        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Ми зв\'яжемося з вами найближчим часом.',
            'telegram_sent': telegram_sent
        })

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'error': "Некоректний формат запиту"
        }, status=400)

    except Exception as e:
        logger.error(f"❌ Unexpected error processing contact form: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': "Сталася помилка. Спробуйте пізніше."
        }, status=500)