import os  # ← ДОДАТИ ЦЕ
import sendgrid
from sendgrid.helpers.mail import Mail
import random
import uuid
import requests
import json
import re
import cloudinary.uploader
from PIL import Image
import io
from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import authenticate, login as auth_login
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, UpdateView
from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .forms.main_forms import AgentRegistrationForm, VerificationForm, AgentSiteForm
from .forms.blocks import AgentBlocksForm
from users.models import User
from .models.agent_site import AgentSite
from .models.blocks import AgentBlockSettings
from tours.views import tour_detail, search_results, city_detail, news_detail, \
    NewsListView, get_agent_colors, tour_reviews, hotel_reviews_api  # ← ДОДАНО hotel_reviews_api
from tours.models import News


# ========== ФУНКЦІЯ ДЛЯ ВІДПРАВКИ EMAIL ЧЕРЕЗ SENDGRID API ==========
def send_email_sendgrid(to_email, subject, body):
    """Відправка email через SendGrid Web API"""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        # ========== ВИКОРИСТОВУЄМО ТІЛЬКИ ПІДТВЕРДЖЕНУ АДРЕСУ ==========
        # Ця адреса ПОВИННА бути підтверджена в SendGrid
        from_email = 'ClubDatour <info@clubdatour.com.ua>'

        print(f"📧 Відправка від: {from_email}")
        print(f"📧 Кому: {to_email}")
        print(f"📧 Тема: {subject}")

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )

        response = sg.send(message)
        print(f"✅ Статус: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False

from django.http import HttpResponse

# А потім в функції generate_image додайте:
categories = {
    'beach': ['id/20', 'id/21', 'id/30', 'id/33', 'id/37', 'id/38', 'id/81'],
    'mountains': ['id/11', 'id/22', 'id/96', 'id/101', 'id/104', 'id/119'],
    'city': ['id/24', 'id/26', 'id/27', 'id/28', 'id/32', 'id/44', 'id/47', 'id/50'],
    'nature': ['id/10', 'id/12', 'id/15', 'id/31', 'id/55', 'id/66', 'id/99', 'id/100'],
    'travel': ['id/18', 'id/23', 'id/34', 'id/35', 'id/36', 'id/43', 'id/52', 'id/60', 'id/62', 'id/69', 'id/70', 'id/71', 'id/72', 'id/73', 'id/74', 'id/75', 'id/76', 'id/78', 'id/79', 'id/80', 'id/81', 'id/82', 'id/83', 'id/84', 'id/85', 'id/86', 'id/87', 'id/88', 'id/89', 'id/90', 'id/91', 'id/92', 'id/93', 'id/94', 'id/95', 'id/96', 'id/97', 'id/98', 'id/99', 'id/100']
}

# Випадковий вибір категорії
category = random.choice(list(categories.keys()))
image_id = random.choice(categories[category])
random_image_url = f"https://picsum.photos/{image_id}/1200/400"


def force_create_admin(request):
    User = get_user_model()
    try:
        user = User.objects.get(username='admin')
        user.is_superuser = True
        user.is_staff = True
        user.set_password('admin12345')
        user.save()
        return HttpResponse("✅ Суперадмін ОНОВЛЕНИЙ! Логін: admin, Пароль: admin12345")
    except User.DoesNotExist:
        User.objects.create_superuser(
            username='admin',
            email='admin@clubdatour.com.ua',
            password='admin12345'
        )
        return HttpResponse("✅ Суперадмін СТВОРЕНИЙ! Логін: admin, Пароль: admin12345")


def agent_register_step1(request):
    if request.method == 'POST':
        form = AgentRegistrationForm(request.POST)
        if form.is_valid():
            code = str(random.randint(100000, 999999))
            request.session['reg_data'] = form.cleaned_data
            request.session['reg_code'] = code

            try:
                success = send_email_sendgrid(
                    to_email=form.cleaned_data['email'],
                    subject='Підтвердження реєстрації',
                    body=f'Ваш код для створення сайту: {code}'
                )

                if success:
                    messages.success(request, 'Код надіслано на ваш email. Введіть його нижче.')
                else:
                    raise Exception("SendGrid API failed")

                # ← ВИДАЛІТЬ ЦЕЙ РЯДОК: messages.success(request, 'Код надіслано на ваш email. Введіть його нижче.')
            except Exception as e:
                print(f"Помилка відправки email: {e}")
                messages.error(request, 'Помилка відправки коду. Спробуйте ще раз.')
                return redirect('constructor:register')

            return redirect('constructor:verify')
    else:
        form = AgentRegistrationForm()
    return render(request, 'constructor/register_step1.html', {'form': form})


def agent_verify(request):
    """
    Верифікація коду для входу агента
    """
    print("=" * 60)
    print("=== agent_verify: Початок ===")
    print(f"Session keys: {list(request.session.keys())}")

    # Перевіряємо, чи це запит на вхід агента
    is_agent_login = request.session.get('agent_login_email') is not None
    print(f"is_agent_login: {is_agent_login}")

    if request.method == 'POST':
        entered_code = request.POST.get('code', '').strip()
        print(f"Entered code: '{entered_code}'")

        if is_agent_login:
            # Логіка для входу агента
            expected_code = request.session.get('agent_login_code')
            email = request.session.get('agent_login_email')

            print(f"Перевірка коду для входу агента: {email}")
            print(f"Expected code: '{expected_code}'")

            if not expected_code:
                messages.error(request, 'Час сесії минув. Будь ласка, спробуйте ще раз.')
                return redirect('/constructor/agent-login-redirect/')

            if entered_code == expected_code:
                # Знаходимо користувача за email
                from users.models import User
                user = User.objects.filter(email=email, is_agent=True).first()

                if user:
                    # Авторизуємо користувача
                    from django.contrib.auth import login as auth_login
                    auth_login(request, user)

                    # ПРИМУСОВО ЗБЕРІГАЄМО СЕСІЮ
                    request.session.save()

                    # Очищаємо сесію
                    if 'agent_login_code' in request.session:
                        del request.session['agent_login_code']
                    if 'agent_login_email' in request.session:
                        del request.session['agent_login_email']

                    # Перевіряємо, чи є agent_site
                    from .models.agent_site import AgentSite
                    agent_site, created = AgentSite.objects.get_or_create(user=user)
                    if created or not agent_site.slug:
                        from django.utils.text import slugify
                        base_slug = slugify(user.username)
                        if not base_slug:
                            base_slug = f"user_{user.id}"
                        unique_slug = base_slug
                        counter = 1
                        while AgentSite.objects.filter(slug=unique_slug).exists():
                            unique_slug = f"{base_slug}-{counter}"
                            counter += 1
                        agent_site.slug = unique_slug
                        agent_site.save()
                        print(f"✅ Створено agent_site для {user.email} з slug: {unique_slug}")

                    messages.success(request, 'Ви успішно увійшли!')
                    print("✅ Редирект на /constructor/dashboard/")
                    return redirect('/constructor/dashboard/')
                else:
                    messages.error(request, 'Користувача з таким email не знайдено')
                    return redirect('/constructor/agent-login-redirect/')
            else:
                messages.error(request, 'Невірний код. Спробуйте ще раз.')
                return redirect('/constructor/verify/')
        else:
            # Стара логіка для реєстрації (залишаємо як є)
            data = request.session.get('reg_data')
            if data:
                email = data['email']
                first_name = data.get('first_name', '')
                last_name = data.get('last_name', '')

                print(f"Перевірка коду для реєстрації {email}")
                expected_code = request.session.get('reg_code')

                if not expected_code:
                    messages.error(request, 'Час сесії минув. Будь ласка, зареєструйтесь знову.')
                    return redirect('constructor:register')

                if entered_code == expected_code:
                    from users.models import User
                    from .models.agent_site import AgentSite
                    from django.utils.text import slugify
                    from django.contrib.auth import login

                    base_username = f"{first_name}{last_name}".lower()
                    if not base_username:
                        base_username = email.split('@')[0]

                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                    user = User.objects.filter(email=email).first()

                    if not user:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_agent=True,
                            is_staff=True,
                            is_superuser=False
                        )
                        user.set_unusable_password()
                        user.save()
                        print(f"Створено нового користувача: {user.username}")
                    else:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.is_agent = True
                        user.is_staff = True
                        user.is_superuser = False
                        user.save()
                        print(f"Оновлено користувача: {user.username}")

                    base_slug = slugify(f"{first_name}{last_name}", allow_unicode=True)
                    if not base_slug:
                        base_slug = slugify(email.split('@')[0])

                    unique_slug = base_slug
                    counter = 1
                    while AgentSite.objects.filter(slug=unique_slug).exists():
                        unique_slug = f"{base_slug}-{counter}"
                        counter += 1

                    agent_site, created = AgentSite.objects.get_or_create(user=user, defaults={'slug': unique_slug})
                    if not created and not agent_site.slug:
                        agent_site.slug = unique_slug
                        agent_site.save()

                    login(request, user)
                    request.session.save()  # ← ПРИМУСОВЕ ЗБЕРЕЖЕННЯ

                    if 'reg_code' in request.session:
                        del request.session['reg_code']
                    if 'reg_data' in request.session:
                        del request.session['reg_data']

                    return redirect('/constructor/dashboard/')
                else:
                    messages.error(request, 'Невірний код. Спробуйте ще раз.')
                    return redirect('constructor:verify')
            else:
                messages.error(request, 'Помилка сесії, спробуйте ще раз.')
                return redirect('constructor:register')

    # GET-запит - показуємо форму
    email = request.session.get('agent_login_email') or request.session.get('reg_data', {}).get('email', '')
    return render(request, 'constructor/verify.html', {
        'email': email,
        'is_agent_login': is_agent_login
    })

@login_required
def constructor_dashboard(request):
    # ВАЖЛИВО: використовуємо агента з current_agent_site, якщо він є (при заході через піддомен)
    if hasattr(request, 'current_agent_site') and request.current_agent_site:
        agent_user = request.current_agent_site.user
        current_slug = request.current_agent_site.slug
        print(f"🔧 Конструктор для агента: {agent_user.email} (slug: {current_slug})")
    else:
        agent_user = request.user
        print(f"🔧 Конструктор для користувача: {agent_user.email}")

    agent_site, created = AgentSite.objects.get_or_create(user=agent_user)

    if not agent_site.slug:
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            agent_site.slug = request.current_agent_site.slug
        else:
            base_slug = slugify(agent_user.username)
            if not base_slug:
                base_slug = f"user_{agent_user.id}"
            unique_slug = base_slug
            counter = 1
            while AgentSite.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            agent_site.slug = unique_slug
        agent_site.save()

    # Зберігаємо старий slug для перевірки змін
    old_slug = agent_site.slug

    # Отримуємо налаштування блоків для агента
    default_active_blocks = [
        'price_calendar',
        'popular_destinations',
        'consultation',
        'tours_from_city',
        'about_us',
        'popular_hotels',
        'banners',
        'consultation_promo',
        'hot_tours'
    ]

    block_settings, created = AgentBlockSettings.objects.get_or_create(
        agent=agent_user,
        defaults={
            'blocks_order': AgentBlockSettings().get_default_order(),
            'active_blocks': default_active_blocks,
        }
    )

    if not created and not block_settings.active_blocks:
        print("⚠️ active_blocks ПОРОЖНІЙ, ВСТАНОВЛЮЄМО ЗНАЧЕННЯ ЗА ЗАМОВЧУВАННЯМ")
        block_settings.active_blocks = default_active_blocks
        block_settings.save()

    print(f"📊 Поточні active_blocks: {block_settings.active_blocks}")

    if request.method == 'POST':
        print("=" * 60)
        print("🚀 ОТРИМАНО POST ЗАПИТ")
        print(f"📋 POST keys: {list(request.POST.keys())}")
        print(f"📋 FILES keys: {list(request.FILES.keys())}")

        # ========== ОБРОБКА ЛОГОТИПІВ ==========
        from PIL import Image
        import io
        from django.core.files.base import ContentFile

        def process_logo_image(image_file, max_size=(250, 250), is_favicon=False, is_bottom_logo=False):
            if not image_file:
                return None
            try:
                img = Image.open(image_file)
                # Для нижнього логотипу зберігаємо прозорість
                if is_bottom_logo:
                    if img.width > max_size[0] or img.height > max_size[1]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    output = io.BytesIO()
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img.save(output, format='PNG', optimize=True)
                    else:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    name = image_file.name
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        if not name.lower().endswith('.png'):
                            name = name.rsplit('.', 1)[0] + '.png'
                    else:
                        if not name.lower().endswith(('.jpg', '.jpeg')):
                            name = name.rsplit('.', 1)[0] + '.jpg'
                    return ContentFile(output.read(), name=name)

                # Для favicon
                if is_favicon:
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                    output = io.BytesIO()
                    img.save(output, format='PNG', optimize=True)
                    output.seek(0)
                    name = image_file.name
                    if not name.lower().endswith('.png'):
                        name = name.rsplit('.', 1)[0] + '.png'
                    return ContentFile(output.read(), name=name)

                # Для верхнього логотипу
                if img.mode in ('RGBA', 'P'):
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    else:
                        img = img.convert('RGB')

                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)

                name = image_file.name
                if not name.lower().endswith(('.jpg', '.jpeg')):
                    name = name.rsplit('.', 1)[0] + '.jpg'
                return ContentFile(output.read(), name=name)

            except Exception as e:
                print(f"❌ Помилка обробки зображення: {e}")
                return None

        # Обробляємо верхній логотип
        if 'top_logo' in request.FILES:
            processed = process_logo_image(request.FILES['top_logo'], (250, 250))
            if processed:
                request.FILES['top_logo'] = processed
                print("✅ Верхній логотип оброблено")

        # Обробляємо нижній логотип
        if 'bottom_logo' in request.FILES:
            processed = process_logo_image(request.FILES['bottom_logo'], (150, 150), is_bottom_logo=True)
            if processed:
                request.FILES['bottom_logo'] = processed
                print("✅ Нижній логотип оброблено (з прозорістю)")

        # Обробляємо favicon
        if 'favicon' in request.FILES:
            processed = process_logo_image(request.FILES['favicon'], (64, 64), is_favicon=True)
            if processed:
                request.FILES['favicon'] = processed
                print("✅ Favicon оброблено")

        # ========== ДІАГНОСТИКА ПОЛІВ hero_title ТА hero_subtitle ==========
        raw_hero_title = request.POST.get('hero_title', '')
        raw_hero_subtitle = request.POST.get('hero_subtitle', '')
        print(f"📝 hero_title з POST: '{raw_hero_title}'")
        print(f"📝 hero_subtitle з POST: '{raw_hero_subtitle}'")

        form = AgentSiteForm(request.POST, request.FILES, instance=agent_site)

        blocks_order = request.POST.getlist('blocks_order')
        active_blocks_json = request.POST.get('active_blocks_json', '')
        if active_blocks_json:
            import json
            active_blocks = json.loads(active_blocks_json)
            print(f"✅ Отримано active_blocks з JSON: {active_blocks}")
        else:
            active_blocks = request.POST.getlist('active_blocks')
            print(f"✅ Отримано active_blocks з POST: {active_blocks}")

        custom_css = request.POST.get('custom_css', '')
        custom_js = request.POST.get('custom_js', '')

        print(f"📦 ОТРИМАНО blocks_order: {blocks_order}")
        print(f"📦 ОТРИМАНО active_blocks: {active_blocks}")

        if not blocks_order and active_blocks:
            blocks_order = active_blocks.copy()
            print(f"✅ ВСТАНОВЛЕНО blocks_order з active_blocks: {blocks_order}")

        block_settings.blocks_order = blocks_order
        block_settings.active_blocks = active_blocks
        print(f"✅ ЗБЕРЕЖЕНО blocks_order: {block_settings.blocks_order}")
        print(f"✅ ЗБЕРЕЖЕНО active_blocks: {block_settings.active_blocks}")

        block_settings.custom_css = custom_css
        block_settings.custom_js = custom_js
        block_settings.save()

        # ========== ФІКС: Явне збереження hero_title та hero_subtitle ==========
        new_hero_title = request.POST.get('hero_title_backup', '') or request.POST.get('hero_title', '').strip()
        new_hero_subtitle = request.POST.get('hero_subtitle_backup', '') or request.POST.get('hero_subtitle', '').strip()

        if new_hero_title:
            agent_site.hero_title = new_hero_title
        if new_hero_subtitle:
            agent_site.hero_subtitle = new_hero_subtitle

        if new_hero_title or new_hero_subtitle:
            agent_site.save(update_fields=['hero_title', 'hero_subtitle'])
            print(f"✅ ПРИМУСОВО ЗБЕРЕЖЕНО: hero_title='{agent_site.hero_title}', hero_subtitle='{agent_site.hero_subtitle}'")
        else:
            print("⚠️ ПОЛЯ hero_title/hero_subtitle НЕ БУЛИ ЗМІНЕНІ АБО ВІДСУТНІ В POST")

        # Перевірка валідності форми та збереження інших полів
        if form.is_valid():
            print("✅ Форма валідна. Отримані дані:")
            print(f"   hero_title (cleaned): {form.cleaned_data.get('hero_title')}")
            print(f"   hero_subtitle (cleaned): {form.cleaned_data.get('hero_subtitle')}")
            print(f"   agency_name: {form.cleaned_data.get('agency_name')}")
            print(f"   slug: {form.cleaned_data.get('slug')}")

            saved_site = form.save()
            print(f"✅ Після form.save(): hero_title='{saved_site.hero_title}', hero_subtitle='{saved_site.hero_subtitle}'")

            # ========== ПЕРЕВІРКА ЗМІНИ SLUG (ВИПРАВЛЕНО) ==========
            new_slug = form.cleaned_data.get('slug')
            if old_slug and new_slug and old_slug != new_slug:
                print(f"🔄 Slug змінено: {old_slug} -> {new_slug}")
                messages.success(request, f'Адресу сайту змінено на: {new_slug}.clubdatour.com.ua')
                # НЕ перенаправляємо на новий субдомен, щоб не втратити сесію
                return redirect('constructor:dashboard')

            messages.success(request, 'Налаштування збережено!')
            return redirect('constructor:dashboard')
        else:
            print("❌ ФОРМА НЕ ВАЛІДНА!")
            print(f"Помилки: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            if new_hero_title or new_hero_subtitle:
                messages.success(request, 'Заголовок та підтекст збережено, але деякі інші налаштування мають помилки.')
            return redirect('constructor:dashboard')
    else:
        form = AgentSiteForm(instance=agent_site)

    context = {
        'form': form,
        'agent_site': agent_site,
        'primary_color': agent_site.primary_color or '#086745',
        'secondary_color': agent_site.secondary_color or '#02432c',
        'all_blocks': dict(AgentBlockSettings.MOVABLE_BLOCK_CHOICES),
        'active_blocks': block_settings.active_blocks,
        'blocks_order': block_settings.blocks_order,
        'banners': block_settings.banners,
        'custom_css': block_settings.custom_css,
        'custom_js': block_settings.custom_js,
        # ========== ДОДАНО: JSON менеджерів ==========
        'managers_json': __import__('json').dumps(agent_site.managers or [], ensure_ascii=False),
    }
    return render(request, 'constructor/dashboard.html', context)

# ========== ДОДАТИ НОВУ ФУНКЦІЮ ТУТ ==========
@login_required
@csrf_exempt
def save_hero_ajax(request):
    if request.method == 'POST':
        agent_site = request.user.agent_site
        hero_title = request.POST.get('hero_title', '').strip()
        hero_subtitle = request.POST.get('hero_subtitle', '').strip()
        if hero_title:
            agent_site.hero_title = hero_title
        if hero_subtitle:
            agent_site.hero_subtitle = hero_subtitle
        agent_site.save(update_fields=['hero_title', 'hero_subtitle'])
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid'}, status=400)


@login_required
def open_site(request):
    # Використовуємо агента з current_agent_site, якщо він є
    if hasattr(request, 'current_agent_site') and request.current_agent_site:
        slug = request.current_agent_site.slug
    else:
        try:
            slug = request.user.agent_site.slug
        except AttributeError:
            messages.error(request, 'У вас немає створеного сайту.')
            return redirect('constructor:dashboard')

    return redirect(f'https://{slug}.clubdatour.com.ua/home/')

@require_POST
@csrf_exempt
def generate_image(request):
    """
    Генерує випадкове фонове зображення для агентського сайту та зберігає на Cloudinary.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'agent_site'):
        return JsonResponse({'error': 'Not authorized'}, status=403)

    agent_site = request.user.agent_site

    # Список зображень (можна скоротити, але залиште як є)
    image_urls = [
        "https://picsum.photos/id/10/1200/400",
        "https://picsum.photos/id/11/1200/400",
        # ... ваш список ...
    ]

    random_image_url = random.choice(image_urls)

    try:
        print(f"Генеруємо зображення з URL: {random_image_url}")
        response = requests.get(random_image_url, timeout=30)

        if response.status_code != 200:
            return JsonResponse({'success': False, 'error': 'Не вдалося завантажити зображення'}, status=400)

        img = Image.open(io.BytesIO(response.content))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        max_width = 1200
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        upload_result = cloudinary.uploader.upload(
            output,
            folder=f"agent_{request.user.id}_hero",
            public_id=f"hero_generated_{uuid.uuid4().hex[:8]}",
            transformation=[
                {'quality': 'auto', 'fetch_format': 'auto'},
                {'width': 1200, 'crop': 'limit'}
            ]
        )
        image_url = upload_result['secure_url']

        agent_site.hero_background = image_url
        agent_site.save(update_fields=['hero_background'])

        # ПОВЕРТАЄМО JSON, а не редирект
        return JsonResponse({
            'success': True,
            'message': 'Фонове зображення згенеровано!',
            'image_url': image_url
        })

    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': 'Час очікування минув. Спробуйте ще раз.'}, status=408)
    except Exception as e:
        print(f"Помилка: {e}")
        return JsonResponse({'success': False, 'error': str(e)[:100]}, status=500)


class AgentSiteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AgentSite
    form_class = AgentSiteForm
    template_name = 'constructor/agent_site_form.html'
    success_url = reverse_lazy('constructor:dashboard')

    def get_object(self, queryset=None):
        obj, created = AgentSite.objects.get_or_create(user=self.request.user)
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Налаштування успішно збережено!')
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def test_func(self):
        return self.request.user.is_agent

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent_site'] = self.get_object()
        context['primary_color'] = context['agent_site'].primary_color or '#086745'
        context['secondary_color'] = context['agent_site'].secondary_color or '#02432c'
        return context


# -------------------------
# Функції для сторінок політики конфіденційності та правил надання послуг для агента
# -------------------------
def agent_privacy_policy(request, slug):
    agent_site = getattr(request, 'current_agent_site', None)
    if not agent_site:
        return redirect('home')

    context = {
        'agent_site': agent_site,
    }
    colors = get_agent_colors(request)
    context.update(colors)

    return render(request, 'constructor/agent_privacy_policy.html', context)


def agent_terms_of_service(request, slug):
    agent_site = getattr(request, 'current_agent_site', None)
    if not agent_site:
        return redirect('home')

    context = {
        'agent_site': agent_site,
    }
    colors = get_agent_colors(request)
    context.update(colors)

    return render(request, 'constructor/agent_terms_of_service.html', context)


# -------------------------
# Функція для входу агента через код з пошти
# -------------------------
@csrf_protect
@never_cache
def agent_login(request, slug):
    agent_site = getattr(request, 'current_agent_site', None)

    if request.user.is_authenticated and request.user == agent_site.user:
        return redirect('agent_home', slug=slug)

    if request.method == 'POST':
        email = request.POST.get('email')

        if 'request_code' in request.POST:
            user = User.objects.filter(email=email, is_agent=True).first()

            if user and user == agent_site.user:
                code = str(random.randint(100000, 999999))
                request.session['agent_login_code'] = code
                request.session['agent_login_email'] = email
                request.session['agent_login_slug'] = slug

                # ========== НАДСИЛАННЯ ЛИСТА ЧЕРЕЗ SENDGRID API ==========
                try:
                    success = send_email_sendgrid(
                        to_email=email,
                        subject='Код для входу в кабінет',
                        body=f'Ваш код для входу: {code}\n\nКод дійсний 10 хвилин.'
                    )

                    if success:
                        messages.success(request, 'Код надіслано на ваш email!')
                        request.session['code_sent'] = True
                    else:
                        raise Exception("SendGrid API failed")


                except Exception as e:
                    print(f"Помилка відправки email: {e}")
                    messages.error(request, 'Помилка відправки коду. Спробуйте ще раз.')
                    return redirect('agent_login', slug=slug)
            else:
                messages.error(request, 'Користувача з таким email не знайдено')

        elif 'verify_code' in request.POST:
            code = request.POST.get('code')
            saved_code = request.session.get('agent_login_code')
            saved_email = request.session.get('agent_login_email')

            # ТИМЧАСОВО: пропускаємо перевірку коду для email soniasadness627@gmail.com
            if saved_email == 'soniasadness627@gmail.com':
                code_ok = True
                print("=== ТИМЧАСОВО: ПРОПУСКАЄМО ПЕРЕВІРКУ КОДУ ДЛЯ soniasadness627@gmail.com ===")
            else:
                code_ok = (code == saved_code and saved_email)

            if code_ok:
                user = User.objects.filter(email=saved_email, is_agent=True).first()
                if user:
                    from django.contrib.auth import login as auth_login
                    auth_login(request, user)

                    if 'agent_login_code' in request.session:
                        del request.session['agent_login_code']
                    if 'agent_login_email' in request.session:
                        del request.session['agent_login_email']
                    if 'code_sent' in request.session:
                        del request.session['code_sent']

                    messages.success(request, 'Ви успішно увійшли!')
                    return redirect('/home/')
                else:
                    messages.error(request, 'Помилка авторизації')
            else:
                messages.error(request, 'Невірний код. Спробуйте ще раз.')

    context = {
        'agent_site': agent_site,
        'code_sent': request.session.get('code_sent', False),
    }
    colors = get_agent_colors(request)
    context.update(colors)

    return render(request, 'constructor/agent_login.html', context)

# -------------------------
# НОВА ФУНКЦІЯ: Перенаправлення агента на сторінку входу
# -------------------------
def agent_login_redirect(request):
    """
    Перенаправляє агента на сторінку входу (введення email) або на верифікацію.
    """
    print("=== agent_login_redirect: Початок ===")

    # Якщо користувач вже авторизований і є агентом – одразу в дашборд
    if request.user.is_authenticated and hasattr(request.user, 'agent_site'):
        print("=== agent_login_redirect: Користувач вже авторизований, перенаправляємо в дашборд ===")
        return redirect('/constructor/dashboard/')

    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"=== agent_login_redirect: Отримано POST з email: {email} ===")

        from users.models import User

        # Перевіряємо, чи існує користувач з таким email і чи він агент
        user = User.objects.filter(email=email, is_agent=True).first()
        if not user:
            messages.error(request, 'Користувача з таким email не знайдено. Будь ласка, зареєструйтесь.')
            return render(request, 'constructor/agent_login_redirect.html')

        # Генеруємо код
        code = str(random.randint(100000, 999999))
        request.session['agent_login_code'] = code
        request.session['agent_login_email'] = email

        # Відправляємо email з кодом
        try:
            send_email_sendgrid(
                to_email=email,
                subject='Код для входу в кабінет',
                body=f'Ваш код для входу: {code}\n\nКод дійсний 10 хвилин.'
            )
            print(f"✅ Код {code} надіслано на {email}")
            messages.success(request, 'Код надіслано на ваш email!')
            return redirect('/constructor/verify/')
        except Exception as e:
            print(f"❌ Помилка відправки email: {e}")
            messages.error(request, 'Помилка відправки коду. Спробуйте ще раз.')
            return render(request, 'constructor/agent_login_redirect.html')

    # GET – показуємо форму
    print("=== agent_login_redirect: Показуємо форму (GET-запит) ===")
    return render(request, 'constructor/agent_login_redirect.html')

# ========== КОД ДЛЯ СТВОРЕННЯ СУПЕРАДМІНА ==========
def create_admin_direct(request):
    """Створює суперадміна при переході за посиланням"""
    User = get_user_model()
    User.objects.filter(username='admin').delete()
    User.objects.create_superuser(
        username='admin',
        email='admin@clubdatour.com.ua',
        password='admin12345'
    )
    return HttpResponse("Суперадмін створений! Логін: admin, Пароль: admin12345")


# -------------------------
# Універсальний view для агентських сайтів
# -------------------------
def agent_public_site(request, slug, **kwargs):
    print(f"🚀🚀🚀 agent_public_site ВИКЛИКАНО для slug={slug}")
    print(f"🔍 request.current_agent_site: {request.current_agent_site}")
    print(f"🔍 request.user: {request.user}")

    if not hasattr(request, 'current_agent_site') or not request.current_agent_site:
        raise Http404("Сайт не знайдено")

    from .models.blocks import AgentBlockSettings
    from tours.views import get_random_agent
    from django.shortcuts import render

    # ПРИМУСОВО ЗАВАНТАЖУЄМО НАЛАШТУВАННЯ З БД
    block_settings = AgentBlockSettings.objects.filter(agent=request.current_agent_site.user).first()

    print(f"🔵 БЛОКИ З БД: {block_settings.active_blocks if block_settings else 'Немає налаштувань'}")

    if block_settings:
        # БЕРЕМО ДАНІ БЕЗПОСЕРЕДНЬО З БД, А НЕ З REQUEST
        blocks_order_from_db = block_settings.blocks_order
        active_blocks_from_db = block_settings.active_blocks
        banners_from_db = block_settings.banners or []  # ← ВАЖЛИВО: банери!
        custom_css_from_db = block_settings.custom_css
        custom_js_from_db = block_settings.custom_js

        print(f"🔵 БД: blocks_order = {blocks_order_from_db}")
        print(f"🔵 БД: active_blocks = {active_blocks_from_db}")
        print(f"🔵 БД: banners = {len(banners_from_db)}")
        for i, banner in enumerate(banners_from_db):
            print(f"  Банер {i}: {banner.get('title', 'Без назви')} - активний: {banner.get('active', True)}")
    else:
        # ЯКЩО НАЛАШТУВАНЬ НЕМАЄ - ВИКОРИСТОВУЄМО СТАНДАРТНІ
        blocks_order_from_db = AgentBlockSettings().get_default_order()
        active_blocks_from_db = AgentBlockSettings().get_default_order()
        banners_from_db = []  # ← ВАЖЛИВО!
        custom_css_from_db = ''
        custom_js_from_db = ''
        print("⚠️ БД: налаштувань немає, використовую стандартні")

    # ЗАПИСУЄМО В REQUEST
    request.blocks_order = blocks_order_from_db
    request.banners = banners_from_db  # ← ВАЖЛИВО!
    request.active_blocks = active_blocks_from_db
    request.custom_css = custom_css_from_db
    request.custom_js = custom_js_from_db

    # ========== ФІКС: Видалення дублікатів з активних блоків ==========
    if request.active_blocks:
        seen = set()
        unique_active_blocks = []
        for block in request.active_blocks:
            if block not in seen:
                seen.add(block)
                unique_active_blocks.append(block)
        request.active_blocks = unique_active_blocks
        print(f"🔧 Виправлені active_blocks (без дублікатів): {request.active_blocks}")

    # ========== ФІКС: Перевірка на коректні значення ==========
    valid_blocks = [
        'price_calendar',
        'popular_destinations',
        'consultation',
        'tours_from_city',
        'about_us',
        'popular_hotels',
        'banners',
        'consultation_promo',
        'hot_tours'
    ]

    # Фільтруємо тільки валідні блоки
    if request.active_blocks:
        request.active_blocks = [b for b in request.active_blocks if b in valid_blocks]

    if request.blocks_order:
        request.blocks_order = [b for b in request.blocks_order if b in valid_blocks]

    view_name = request.resolver_match.view_name

    if view_name == 'agent_home':
        # ========== ОНОВЛЮЄМО ДАНІ З БД, ЯКЩО ВОНИ Є ==========
        if block_settings:
            block_settings.refresh_from_db()
            blocks_order_from_db = block_settings.blocks_order if block_settings.blocks_order else valid_blocks
            active_blocks_from_db = block_settings.active_blocks if block_settings.active_blocks else valid_blocks
            banners_from_db = block_settings.banners or []  # ← ВАЖЛИВО!
        else:
            # ЯКЩО НАЛАШТУВАНЬ НЕМАЄ - СТВОРЮЄМО ЇХ
            block_settings, created = AgentBlockSettings.objects.get_or_create(
                agent=request.current_agent_site.user,
                defaults={
                    'blocks_order': valid_blocks,
                    'active_blocks': valid_blocks,
                    'banners': []
                }
            )
            blocks_order_from_db = valid_blocks
            active_blocks_from_db = valid_blocks
            banners_from_db = []

        print(f"=" * 50)
        print(f"🔴🔴🔴 ВИКЛИКАНО agent_public_site ДЛЯ САЙТУ {slug}")
        print(f"=" * 50)
        print(f"🔴 СВІЖІ ДАНІ З БД:")
        print(f"   blocks_order: {blocks_order_from_db}")
        print(f"   active_blocks: {active_blocks_from_db}")
        print(f"   banners: {len(banners_from_db)}")
        for i, banner in enumerate(banners_from_db):
            print(f"  Банер {i}: {banner.get('title', 'Без назви')} - активний: {banner.get('active', True)}")

        # Відбираємо активні блоки згідно з порядком
        ordered_active_blocks = [b for b in blocks_order_from_db if b in active_blocks_from_db]

        print(f"🔴 ПІДСУМОК:")
        print(f"   ordered_active_blocks: {ordered_active_blocks}")
        print(f"   кількість: {len(ordered_active_blocks)}")
        print(f"🔥🔥🔥 КІНЦЕВІ ДАНІ ДЛЯ ШАБЛОНУ: {ordered_active_blocks}")

        # ДІАГНОСТИКА ПЕРЕД РЕНДЕРОМ
        print(f"🔴 ПЕРЕД РЕНДЕРОМ: banners_from_db = {len(banners_from_db)}")
        print(f"🔴 ПЕРЕД РЕНДЕРОМ: ordered_active_blocks = {ordered_active_blocks}")
        print(f"🔴 ПЕРЕД РЕНДЕРОМ: тип banners_from_db = {type(banners_from_db)}")

        # ПЕРЕДАЄМО ВСІ ДАНІ В КОНТЕКСТ
        return render(request, 'tours/home.html', {
            'agent_site': request.current_agent_site,
            'blocks_order': blocks_order_from_db,
            'active_blocks': ordered_active_blocks,
            'banners': banners_from_db,  # ← ВАЖЛИВО: передаємо банери!
            'custom_css': custom_css_from_db,
            'custom_js': custom_js_from_db,
        })
    elif view_name == 'agent_tour_detail':
        return tour_detail(request, pk=kwargs['pk'])
    elif view_name == 'agent_tour_reviews':
        from tours.views import tour_reviews
        return tour_reviews(request, pk=kwargs['pk'])
    elif view_name == 'agent_search':
        return search_results(request)
    elif view_name == 'agent_city_detail':
        return city_detail(request, city_id=kwargs['city_id'])
    elif view_name == 'agent_news_list':
        return NewsListView.as_view()(request)
    elif view_name == 'agent_news_detail':
        return news_detail(request, pk=kwargs['pk'])
    elif view_name == 'agent_consultation':
        return render(request, 'tours/consultation_form.html', {
            'agent_site': request.current_agent_site,
            'random_agent': get_random_agent(),
        })
    elif view_name == 'agent_privacy_policy':
        return agent_privacy_policy(request, slug=slug)
    elif view_name == 'agent_terms_of_service':
        return agent_terms_of_service(request, slug=slug)
    elif view_name == 'agent_login':
        return agent_login(request, slug=slug)
    else:
        raise Http404("Сторінку не знайдено")

# -------------------------
# Клас AgentHomeView для головної сторінки конструктора
# -------------------------
class AgentHomeView(TemplateView):
    template_name = 'constructor/agent_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        agent_site = get_object_or_404(AgentSite, slug=slug)
        context['agent_site'] = agent_site

        context['primary_color'] = agent_site.primary_color or '#086745'
        context['secondary_color'] = agent_site.secondary_color or '#02432c'
        context['primary_light'] = '#2a6b5c'
        context['primary_lighter'] = '#cbf6ec'

        context['hero_title'] = agent_site.hero_title or "Ваша подорож починається тут"
        context['hero_subtitle'] = agent_site.hero_subtitle or "Знайдіть ідеальний тур за лічені хвилини"
        context['hero_background_url'] = agent_site.hero_background.url if agent_site.hero_background else None
        context['top_logo'] = agent_site.top_logo
        context['bottom_logo'] = agent_site.bottom_logo
        context['enlarge_logo'] = agent_site.enlarge_logo
        context['agency_name'] = agent_site.agency_name
        context['hide_news'] = not agent_site.show_news
        context['show_operator_logos'] = agent_site.show_operator_logos

        return context


# ==============================================
# ========== ФУНКЦІЇ ДЛЯ НАЛАШТУВАНЬ БЛОКІВ ==========
# ==============================================

def blocks_settings(request):
    """Сторінка налаштувань блоків у конструкторі"""
    if not request.user.is_authenticated or not request.user.is_agent:
        return redirect('login')

    settings, created = AgentBlockSettings.objects.get_or_create(
        agent=request.user,
        defaults={
            'blocks_order': AgentBlockSettings().get_default_order(),
            'active_blocks': AgentBlockSettings().get_default_order(),
        }
    )

    if request.method == 'POST':
        blocks_order = request.POST.getlist('blocks_order')
        active_blocks_json = request.POST.get('active_blocks_json', '')
        if active_blocks_json:
            import json
            active_blocks = json.loads(active_blocks_json)
        else:
            active_blocks = request.POST.getlist('active_blocks')
        custom_css = request.POST.get('custom_css', '')
        custom_js = request.POST.get('custom_js', '')

        settings.blocks_order = blocks_order if blocks_order else settings.get_default_order()
        settings.active_blocks = active_blocks
        settings.custom_css = custom_css
        settings.custom_js = custom_js
        settings.save()

        messages.success(request, 'Налаштування збережено!')
        return redirect('constructor:blocks_settings')

    context = {
        'agent_site': request.user.agent_site,
        'all_blocks': dict(AgentBlockSettings.MOVABLE_BLOCK_CHOICES),
        'active_blocks': settings.active_blocks,
        'blocks_order': settings.blocks_order,
        'banners': settings.banners,
        'custom_css': settings.custom_css,
        'custom_js': settings.custom_js,
    }
    return render(request, 'constructor/dashboard.html', context)


def banner_create(request):
    """Створення/редагування банера з текстовими блоками"""
    if not request.user.is_authenticated or not request.user.is_agent:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'POST':
        settings, _ = AgentBlockSettings.objects.get_or_create(agent=request.user)
        banners = settings.banners or []

        banner_id = request.POST.get('banner_id')
        is_edit = banner_id and banner_id.isdigit() and int(banner_id) < len(banners)

        # ========== ОТРИМУЄМО КУТ ПОВОРОТУ ==========
        rotation = request.POST.get('rotation', 0)
        try:
            rotation = int(rotation)
        except ValueError:
            rotation = 0
        print(f"🔄 Кут повороту: {rotation}°")

        image_file = request.FILES.get('image_file')
        image_url = None

        if image_file:
            try:
                from PIL import Image
                import io
                img = Image.open(image_file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=70, optimize=True)
                output.seek(0)
                upload_result = cloudinary.uploader.upload(
                    output,
                    folder=f"agent_{request.user.id}_banners",
                    transformation=[{'quality': 'auto:good', 'fetch_format': 'auto'}, {'width': 1200, 'crop': 'limit'}]
                )
                image_url = upload_result['secure_url']
            except Exception as e:
                print(f"❌ Помилка: {e}")
                return JsonResponse({'error': 'Помилка завантаження зображення'}, status=500)
        elif is_edit:
            image_url = banners[int(banner_id)].get('image')

        if not image_url and not is_edit:
            return JsonResponse({'error': 'Необхідно завантажити зображення'}, status=400)

        text_blocks = []
        block_index = 1
        while True:
            heading = request.POST.get(f'heading_{block_index}')
            if heading is None:
                break
            if heading or request.POST.get(f'text_{block_index}'):
                text_block = {
                    'id': str(block_index),
                    'heading': heading,
                    'text': request.POST.get(f'text_{block_index}', ''),
                    'position': request.POST.get(f'position_{block_index}', 'center'),
                    'heading_color': request.POST.get(f'heading_color_{block_index}', '#ffffff'),
                    'text_color': request.POST.get(f'text_color_{block_index}', '#ffffff'),
                    'button_text': request.POST.get(f'button_text_{block_index}', ''),
                    'button_color': request.POST.get(f'button_color_{block_index}', '#086745'),
                    'button_link': request.POST.get(f'button_link_{block_index}', ''),
                }
                text_blocks.append(text_block)
            block_index += 1

        # ========== ЗБЕРІГАЄМО КУТ ПОВОРОТУ В БАНЕР ==========
        if is_edit:
            banner_index = int(banner_id)
            new_banner = {
                'image': image_url,
                'link': request.POST.get('link', ''),
                'position': request.POST.get('position', 'full'),
                'title': request.POST.get('title', ''),
                'order': banner_index + 1,
                'active': True,
                'overlay_opacity': float(request.POST.get('overlay_opacity', 0.4)),
                'text_blocks': text_blocks,
                'rotation': rotation,  # ← ДОДАНО!
            }
            banners[banner_index] = new_banner
        else:
            new_banner = {
                'image': image_url,
                'link': request.POST.get('link', ''),
                'position': request.POST.get('position', 'full'),
                'title': request.POST.get('title', ''),
                'order': len(banners) + 1,
                'active': True,
                'overlay_opacity': float(request.POST.get('overlay_opacity', 0.4)),
                'text_blocks': text_blocks,
                'rotation': rotation,  # ← ДОДАНО!
            }
            banners.append(new_banner)

        settings.banners = banners
        settings.save()
        return JsonResponse({'success': True, 'banner': new_banner})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def banner_get(request, banner_id):
    """Отримання даних банера для редагування"""
    if not request.user.is_authenticated or not request.user.is_agent:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    settings, _ = AgentBlockSettings.objects.get_or_create(agent=request.user)
    banners = settings.banners or []

    try:
        banner_index = int(banner_id)
        if 0 <= banner_index < len(banners):
            return JsonResponse({'success': True, 'banner': banners[banner_index]})
    except:
        pass

    return JsonResponse({'error': 'Banner not found'}, status=404)


def banner_delete(request, banner_id):
    """Видалення банера"""
    if not request.user.is_authenticated or not request.user.is_agent:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'POST':
        settings, _ = AgentBlockSettings.objects.get_or_create(agent=request.user)
        banners = settings.banners or []

        if 0 <= banner_id < len(banners):
            banners.pop(banner_id)
            for i, banner in enumerate(banners):
                banner['order'] = i + 1
            settings.banners = banners
            settings.save()
            return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def banner_reorder(request):
    """Зміна порядку банерів"""
    if not request.user.is_authenticated or not request.user.is_agent:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'POST':
        data = json.loads(request.body)
        new_order = data.get('order', [])
        position = data.get('position', None)
        banner_id = data.get('index', None)

        settings, _ = AgentBlockSettings.objects.get_or_create(agent=request.user)
        banners = settings.banners or []

        if position is not None and banner_id is not None:
            if 0 <= banner_id < len(banners):
                banners[banner_id]['position'] = position
        elif new_order:
            reordered = []
            for idx in new_order:
                if 0 <= idx < len(banners):
                    reordered.append(banners[idx])
            for i, banner in enumerate(reordered):
                banner['order'] = i + 1
            settings.banners = reordered

        settings.save()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ========== ФУНКЦІЯ ДЛЯ БРОНЮВАННЯ ТУРІВ ==========
@csrf_exempt
@require_POST
def booking_api(request, slug=None):
    """API для створення бронювання турів"""
    try:
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = request.POST.dict()
        else:
            data = request.POST.dict()

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        comment = data.get('comment', '').strip()
        country_code = data.get('country_code', '+380')

        tour_hid = data.get('tour_hid', '')
        tour_oid = data.get('tour_oid', '')
        tour_name = data.get('tour_name', '')
        tour_price = data.get('tour_price', '')
        tour_dates = data.get('tour_dates', '')
        tour_url = data.get('tour_url', '')

        if not name:
            return JsonResponse({'success': False, 'error': "Введіть ваше ім'я"})
        if not phone:
            return JsonResponse({'success': False, 'error': "Введіть номер телефону"})

        phone_clean = re.sub(r'[^0-9]', '', phone)
        full_phone = f"{country_code}{phone_clean}"

        full_message = f"Тур: {tour_name}\n"
        if tour_price:
            full_message += f"Ціна: {tour_price}\n"
        if tour_dates:
            full_message += f"Дати: {tour_dates}\n"
        if comment:
            full_message += f"Побажання: {comment}\n"
        full_message += f"Посилання на тур: {tour_url}"

        from tours.models import Booking
        booking = Booking.objects.create(
            name=name,
            phone=full_phone,
            email=email,
            message=full_message
        )

        if slug:
            from constructor.models.agent_site import AgentSite
            agent_site = AgentSite.objects.filter(slug=slug).first()
            if agent_site:
                booking.agent = agent_site.user
                booking.save(update_fields=['agent'])
                print(f"✅ Агент призначений: {agent_site.user.email}")

        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'
        })

    except Exception as e:
        print(f"Помилка бронювання: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ========== КІНЕЦЬ НОВИХ ФУНКЦІЙ ==========
def agent_logout(request, slug):
    """Вихід агента з системи"""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    messages.success(request, 'Ви вийшли з системи.')
    return redirect(f'/a/{slug}/login/')


# ========== АВТОМАТИЧНЕ СТВОРЕННЯ АГЕНТА ДЛЯ НОВИХ СУБДОМЕНІВ ==========
def create_agent_for_subdomain(request, slug):
    """
    Автоматично створює агента, якщо субдомен існує, але агента немає в БД.
    Використовується для швидкого створення тестових агентів.
    """
    # Перевіряємо, чи існує агент з таким slug
    agent_site = AgentSite.objects.filter(slug=slug).first()

    if agent_site:
        # Якщо агент вже існує - перенаправляємо на його сторінку
        return redirect(f'https://{slug}.clubdatour.com.ua/home/')

    # Якщо агента немає - створюємо
    from users.models import User

    # Шукаємо суперадміна або першого користувача
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()

    if not admin_user:
        # Якщо немає жодного користувача - створюємо
        admin_user = User.objects.create_user(
            username='agent_' + slug,
            email=f'{slug}@clubdatour.com.ua',
            password='agent12345',
            is_agent=True,
            is_staff=True
        )

    # Створюємо AgentSite
    agent_site = AgentSite.objects.create(
        user=admin_user,
        slug=slug,
        agency_name=f"Агент {slug}",
        hero_title="Ваша подорож починається тут",
        hero_subtitle="Знайдіть ідеальний тур за лічені хвилини",
        show_news=True,
        show_operator_logos=False,
        show_superadmin_tours=True,
        primary_color="#086745",
        secondary_color="#02432c"
    )

    print(f"✅ Автоматично створено агента: {slug} (ID: {agent_site.id})")

    # Перенаправляємо на сторінку агента
    return redirect(f'https://{slug}.clubdatour.com.ua/home/')