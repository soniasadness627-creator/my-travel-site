
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from .models import AgentSite


class AgentSiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
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
        else:
            print(f"ℹ️ AgentSiteMiddleware: шлях {path} не починається з 'a/'")


class SubdomainMiddleware(MiddlewareMixin):
    """Визначає агента за субдоменом (наприклад, sonia45.clubdatour.com.ua)"""

    def process_request(self, request):
        # Якщо вже є current_agent_site через основний шлях - не чіпаємо
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            return

        # Отримуємо домен без порту
        host = request.get_host().split(':')[0]

        # Розділяємо на частини
        parts = host.split('.')

        # Якщо це субдомен (більше 2 частин, наприклад: sonia45.clubdatour.com.ua)
        if len(parts) >= 3:
            subdomain = parts[0]  # sonia45

            # Перевіряємо, чи не це основний домен (www теж не рахуємо)
            if subdomain in ['www', 'clubdatour', 'clubdatour.com', 'clubdatour.com.ua']:
                return

            # Шукаємо агента з таким slug
            try:
                agent_site = AgentSite.objects.select_related('user').get(slug=subdomain)
                request.current_agent_site = agent_site
                request.agent_subdomain = subdomain
                print(f"✅ SubdomainMiddleware: знайдено агента для субдомену {subdomain}")
            except AgentSite.DoesNotExist:
                print(f"❌ SubdomainMiddleware: агент для субдомену {subdomain} не знайдено")
                request.current_agent_site = None


class AgentColorsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Кольори за замовчуванням
        default_colors = {
            'primary_color': '#086745',
            'primary_dark': '#02432c',
            'primary_light': '#2a6b5c',
            'primary_lighter': '#cbf6ec',
        }

        print("🎨 AgentColorsMiddleware: початок обробки")

        # Якщо є агентський сайт, беремо його кольори
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            site = request.current_agent_site
            print(f"🎨 Знайдено агентський сайт: {site.slug}")
            print(f"🎨 primary_color з БД: {site.primary_color}")
            print(f"🎨 secondary_color з БД: {site.secondary_color}")

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
                primary_light = f"#{r_light:02x}{g_light:02x}{b_light:02x}"
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
            print(f"🎨 Встановлено кольори: primary={primary}, primary_dark={secondary}")
        else:
            request.agent_colors = default_colors
            print("🎨 Використовуються кольори за замовчуванням")

        print(f"🎨 Підсумкові request.agent_colors: {request.agent_colors}")


class DatabaseConnectionMiddleware(MiddlewareMixin):
    """Автоматично перевіряє та відновлює з'єднання з БД перед кожним запитом"""

    def process_request(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            # Якщо з'єднання впало, закриваємо його, щоб створити нове
            connection.close()
            try:
                connection.ensure_connection()
            except Exception:
                pass  # Якщо все ще не працює, наступний запит створить нове з'єднання
        return None