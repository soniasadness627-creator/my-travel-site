from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.urls import reverse
from .models import AgentSite


class AgentSiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Якщо вже є current_agent_site через субдомен - пропускаємо
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            return None

        request.current_agent_site = None
        path = request.path_info.lstrip('/')

        if path.startswith('a/'):
            parts = path.split('/')
            if len(parts) >= 2:
                slug = parts[1]
                try:
                    agent_site = AgentSite.objects.select_related('user').get(slug=slug)
                    request.current_agent_site = agent_site
                    print(f"✅ AgentSiteMiddleware: знайдено сайт для slug={slug}")
                except AgentSite.DoesNotExist:
                    print(f"❌ AgentSiteMiddleware: сайт для slug={slug} не знайдено")
        return None


class SubdomainMiddleware(MiddlewareMixin):
    """Визначає агента за субдоменом (наприклад, stank23565vdf.clubdatour.com.ua)"""

    def process_request(self, request):
        # Отримуємо домен без порту
        host = request.get_host().split(':')[0]

        # СПИСОК ГОЛОВНИХ ДОМЕНІВ (НЕ ПІДДОМЕНИ)
        MAIN_DOMAINS = ['clubdatour.com.ua', 'www.clubdatour.com.ua', '209.38.199.98']

        # 1. Якщо це головний домен - не чіпаємо, показуємо лендінг
        if host in MAIN_DOMAINS:
            request.current_agent_site = None
            request.is_agent_subdomain = False
            print(f"🏠 SubdomainMiddleware: головний домен {host} - показуємо лендінг")
            return None

        # Розділяємо на частини
        parts = host.split('.')

        # Якщо це субдомен (більше 2 частин)
        if len(parts) >= 3:
            subdomain = parts[0]  # stank23565vdf або sonias22

            # Перевіряємо, чи не це службовий субдомен
            if subdomain in ['www', 'mail', 'email', 'smtp', 'pop', 'imap']:
                request.current_agent_site = None
                request.is_agent_subdomain = False
                return None

            # 2. ІГНОРУЄМО ВАШ ОСОБИСТИЙ ПІДДОМЕН (sonias22)
            #    Він не повинен показувати лендінг чи щось інше.
            if subdomain == 'sonias22':
                print(f"🚫 SubdomainMiddleware: субдомен {subdomain} заблоковано для показу сайту.")
                request.current_agent_site = None
                request.is_agent_subdomain = False
                return None

            # 3. ШУКАЄМО ЗВИЧАЙНОГО АГЕНТА
            try:
                agent_site = AgentSite.objects.select_related('user').get(slug=subdomain)
                request.current_agent_site = agent_site
                request.is_agent_subdomain = True
                request.agent_subdomain = subdomain
                print(f"✅ SubdomainMiddleware: знайдено агента для субдомену {subdomain}")
            except AgentSite.DoesNotExist:
                print(f"❌ SubdomainMiddleware: агент для субдомену {subdomain} не знайдено")
                request.current_agent_site = None
                request.is_agent_subdomain = False
        else:
            request.current_agent_site = None
            request.is_agent_subdomain = False

        return None


class AgentColorsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Кольори за замовчуванням
        default_colors = {
            'primary_color': '#086745',
            'primary_dark': '#02432c',
            'primary_light': '#2a6b5c',
            'primary_lighter': '#cbf6ec',
        }

        # Якщо є агентський сайт, беремо його кольори
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            site = request.current_agent_site
            primary = site.primary_color or '#086745'
            secondary = site.secondary_color or '#02432c'

            # Розраховуємо світлі варіанти
            try:
                r = int(primary[1:3], 16)
                g = int(primary[3:5], 16)
                b = int(primary[5:7], 16)
                r_light = min(r + 80, 255)
                g_light = min(g + 80, 255)
                b_light = min(b + 80, 255)
                r_lighter = min(r + 180, 255)
                g_lighter = min(g + 180, 255)
                b_lighter = min(b + 180, 255)
                primary_light = f"#{r_light:02x}{g_light:02x}{b_lighter:02x}"
                primary_lighter = f"#{r_lighter:02x}{g_lighter:02x}{b_lighter:02x}"
            except:
                primary_light = '#2a6b5c'
                primary_lighter = '#cbf6ec'

            request.agent_colors = {
                'primary_color': primary,
                'primary_dark': secondary,
                'primary_light': primary_light,
                'primary_lighter': primary_lighter,
            }
        else:
            request.agent_colors = default_colors

        return None


class DatabaseConnectionMiddleware(MiddlewareMixin):
    """Автоматично перевіряє та відновлює з'єднання з БД перед кожним запитом"""
    def process_request(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            connection.close()
            try:
                connection.ensure_connection()
            except Exception:
                pass
        return None