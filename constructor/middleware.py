from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import AgentSite


class RestrictAdminAccessMiddleware(MiddlewareMixin):
    """Забороняє агентам доступ до /admin/, перенаправляє на /a/admin/"""

    def process_request(self, request):
        # Перевіряємо чи запит до /admin/ або /admin/constructor/
        if request.path.startswith('/admin/'):
            # Якщо користувач авторизований і є агентом (але не суперадміном)
            if request.user.is_authenticated and hasattr(request.user,
                                                         'is_agent') and request.user.is_agent and not request.user.is_superuser:
                # Перенаправляємо на агентську адмінку
                return HttpResponseRedirect('/a/admin/')
        return None


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
                    agent_site = AgentSite.objects.select_related('user').get(slug__iexact=slug)
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
            if subdomain == 'sonias22':
                print(f"🚫 SubdomainMiddleware: субдомен {subdomain} заблоковано для показу сайту.")
                request.current_agent_site = None
                request.is_agent_subdomain = False
                return None

            # 3. ШУКАЄМО ЗВИЧАЙНОГО АГЕНТА (БЕЗ ВРАХУВАННЯ РЕГІСТРУ)
            try:
                agent_site = AgentSite.objects.select_related('user').get(slug__iexact=subdomain)
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

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Обробляє URL перед викликом view"""

        # Якщо це запит до /landing/ на субдомені - перенаправляємо на головний домен
        if request.path.startswith('/landing/'):
            host = request.get_host().split(':')[0]
            # Перевіряємо, чи це не головний домен
            if host not in ['clubdatour.com.ua', 'www.clubdatour.com.ua', '209.38.199.98']:
                print(f"🔄 SubdomainMiddleware: перенаправлення з {host}/landing/ на clubdatour.com.ua/landing/")
                return redirect('https://clubdatour.com.ua/landing/')

        # Якщо це запит до кореня субдомену (без /home/) - додаємо /home/
        if hasattr(request, 'is_agent_subdomain') and request.is_agent_subdomain:
            if request.path == '/' or request.path == '':
                slug = request.agent_subdomain
                print(f"🔄 SubdomainMiddleware: перенаправлення з {slug}.clubdatour.com.ua/ на /home/")
                return redirect('/home/')

        # ========== ВИПРАВЛЕННЯ: ПРИБИРАЄМО /a/slug/ З URL НА СУБДОМЕНІ ==========
        # Якщо це субдомен і шлях починається з /a/, видаляємо цю частину
        if hasattr(request, 'is_agent_subdomain') and request.is_agent_subdomain:
            if request.path.startswith('/a/'):
                # Перевіряємо, чи це не адмінка агента (/a/admin/)
                if not request.path.startswith('/a/admin/'):
                    # Видаляємо /a/slug/ з початку шляху
                    parts = request.path.split('/')
                    if len(parts) >= 3:
                        # Беремо частину після /a/slug/
                        new_path = '/' + '/'.join(parts[3:])
                        if not new_path:
                            new_path = '/'
                        # Додаємо параметри запиту, якщо вони є
                        query_string = request.META.get('QUERY_STRING', '')
                        if query_string:
                            new_path += '?' + query_string
                        print(f"🔄 SubdomainMiddleware: виправляємо URL з {request.path} на {new_path}")
                        return redirect(new_path)

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


class LandingRedirectMiddleware(MiddlewareMixin):
    """Перенаправляє запити до /landing/ на субдоменах на головний домен"""

    def process_request(self, request):
        # Якщо шлях починається з /landing/
        if request.path.startswith('/landing/'):
            host = request.get_host().split(':')[0]
            # Якщо це субдомен (не головний домен)
            if host not in ['clubdatour.com.ua', 'www.clubdatour.com.ua', '209.38.199.98']:
                print(f"🔄 LandingRedirectMiddleware: {host}/landing/ -> clubdatour.com.ua/landing/")
                return redirect('https://clubdatour.com.ua/landing/')
        return None