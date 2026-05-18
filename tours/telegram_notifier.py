import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_notification(message):
    """Надсилає сповіщення всім адміністраторам Telegram бота"""

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    admin_ids = getattr(settings, 'TELEGRAM_ADMIN_IDS', [])

    if not token or not admin_ids:
        logger.warning("Telegram not configured")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    success_count = 0
    for admin_id in admin_ids:
        try:
            response = requests.post(
                api_url,
                json={
                    'chat_id': admin_id,
                    'text': message,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': True
                },
                timeout=10
            )

            if response.status_code == 200:
                success_count += 1
                logger.info(f"Sent to admin {admin_id}")
            else:
                logger.error(f"Failed to send to {admin_id}: {response.text}")

        except Exception as e:
            logger.error(f"Error sending to {admin_id}: {e}")

    return success_count > 0


def send_contact_notification(name, phone, agency, message):
    """Відправляє сповіщення про нову заявку з лендінгу"""

    notification = f"""
<b>📋 НОВА ЗАЯВКА З ЛЕНДІНГУ!</b>

<b>👤 Ім'я:</b> {name}
<b>📞 Телефон:</b> {phone}
<b>🏢 Агенція:</b> {agency or 'Не вказано'}

<b>💬 Повідомлення:</b>
{message or 'Не залишено'}

---
<i>Час: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>
"""
    return send_telegram_notification(notification)


def send_agent_registration_notification(agent_name, agent_email, agent_phone, site_slug):
    """Відправляє сповіщення про реєстрацію нового агента"""

    notification = f"""
<b>🎉 НОВИЙ АГЕНТ ЗАРЕЄСТРУВАВСЯ!</b>

<b>👤 Ім'я:</b> {agent_name}
<b>📧 Email:</b> {agent_email}
<b>📞 Телефон:</b> {agent_phone or 'Не вказано'}

<b>🔗 Посилання на сайт:</b>
https://clubdatour.com.ua/a/{site_slug}/

<i>Агент може увійти в кабінет через email</i>
"""
    return send_telegram_notification(notification)