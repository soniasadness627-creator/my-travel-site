import random
import uuid
import requests
import json
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
from django.http import Http404, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model  # ДОДАНО: імпорт для create_admin_direct
from .forms.main_forms import AgentRegistrationForm, VerificationForm, AgentSiteForm
from .forms.blocks import AgentBlocksForm
from users.models import User
from .models.agent_site import AgentSite
from .models.blocks import AgentBlockSettings
from tours.views import TourListView, tour_detail, search_results, city_detail, news_detail, ConsultationCreateView, \
    NewsListView, get_agent_colors, tour_reviews
from tours.models import News

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
            send_mail(
                subject='Підтвердження реєстрації',
                message=f'Ваш код для створення сайту: {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[form.cleaned_data['email']],
                fail_silently=False,
            )
            messages.success(request, 'Код надіслано на ваш email. Введіть його нижче.')
            return redirect('constructor:verify')
    else:
        form = AgentRegistrationForm()
    return render(request, 'constructor/register_step1.html', {'form': form})


def agent_verify(request):
    """
    Верифікація коду з email - НОРМАЛЬНА РОБОТА
    """
    print("=== agent_verify: Початок ===")

    if request.method == 'POST':
        data = request.session.get('reg_data')
        if data:
            email = data['email']
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')

            print(f"Перевірка коду для {email}")

            entered_code = request.POST.get('code')
            expected_code = request.session.get('reg_code')

            print(f"Entered code: {entered_code}")
            print(f"Expected code: {expected_code}")

            if not expected_code:
                messages.error(request, 'Час сесії минув. Будь ласка, зареєструйтесь знову.')
                return redirect('constructor:register')

            if entered_code == expected_code:
                from users.models import User
                from .models.agent_site import AgentSite
                from django.utils.text import slugify
                from django.contrib.auth import login

                # Створюємо username з імені та прізвища
                base_username = f"{first_name}{last_name}".lower()
                if not base_username:
                    base_username = email.split('@')[0]

                # Робимо username унікальним
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Шукаємо користувача за email
                user = User.objects.filter(email=email).first()

                if not user:
                    # Створюємо нового користувача з username з імені
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_agent=True,
                        is_staff=True
                    )
                    user.set_unusable_password()
                    user.save()
                    print(f"Створено нового користувача: {user.username} (ID: {user.id})")
                else:
                    # Оновлюємо існуючого користувача
                    user.first_name = first_name
                    user.last_name = last_name
                    user.is_agent = True
                    user.is_staff = True
                    user.save()
                    print(f"Оновлено користувача: {user.username}")

                # Створюємо або отримуємо агентський сайт
                base_slug = slugify(f"{first_name}{last_name}".lower())
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

                print(f"Агентський сайт: {agent_site.slug}, створено: {created}")

                login(request, user)

                # Очищаємо сесію
                if 'reg_code' in request.session:
                    del request.session['reg_code']
                if 'reg_data' in request.session:
                    del request.session['reg_data']

                return redirect('/constructor/dashboard/')
            else:
                messages.error(request, 'Невірний код. Спробуйте ще раз.')
                return redirect('constructor:verify')
        else:
            print("Немає даних в сесії reg_data")
            messages.error(request, 'Помилка сесії, спробуйте ще раз.')
            return redirect('constructor:register')

    # GET-запит - показуємо форму
    form = VerificationForm()
    return render(request, 'constructor/verify.html', {
        'form': form,
        'email': request.session.get('reg_data', {}).get('email', '')
    })


@login_required
def constructor_dashboard(request):
    agent_site, created = AgentSite.objects.get_or_create(user=request.user)

    if not agent_site.slug:
        base_slug = slugify(request.user.username)
        if not base_slug:
            base_slug = f"user_{request.user.id}"
        unique_slug = base_slug
        counter = 1
        while AgentSite.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        agent_site.slug = unique_slug
        agent_site.save()

    # Отримуємо налаштування блоків для агента
    block_settings, _ = AgentBlockSettings.objects.get_or_create(
        agent=request.user,
        defaults={
            'blocks_order': AgentBlockSettings().get_default_order(),
            'active_blocks': AgentBlockSettings().get_default_order(),
        }
    )

    if request.method == 'POST':
        # Обробляємо основну форму
        form = AgentSiteForm(request.POST, request.FILES, instance=agent_site)

        # ========== ОБРОБКА НАЛАШТУВАНЬ БЛОКІВ ==========
        blocks_order = request.POST.getlist('blocks_order')
        active_blocks = request.POST.getlist('active_blocks')
        custom_css = request.POST.get('custom_css', '')
        custom_js = request.POST.get('custom_js', '')

        print(f"=== ОТРИМАНО blocks_order: {blocks_order} ===")
        print(f"=== ОТРИМАНО active_blocks: {active_blocks} ===")

        if blocks_order:
            block_settings.blocks_order = blocks_order
        if active_blocks:
            block_settings.active_blocks = active_blocks
        block_settings.custom_css = custom_css
        block_settings.custom_js = custom_js
        block_settings.save()

        print(f"=== ЗБЕРЕЖЕНО blocks_order: {block_settings.blocks_order} ===")

        if form.is_valid():
            saved_site = form.save()
            messages.success(request, 'Налаштування збережено!')
            return redirect('constructor:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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
    }
    return render(request, 'constructor/dashboard.html', context)


@login_required
def open_site(request):
    try:
        slug = request.user.agent_site.slug
        return redirect(f'/a/{slug}/')
    except AttributeError:
        messages.error(request, 'У вас немає створеного сайту.')
        return redirect('constructor:dashboard')


@require_POST
@csrf_exempt
def generate_image(request):
    """
    Генерує випадкове фонове зображення для агентського сайту та зберігає на Cloudinary.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'agent_site'):
        return JsonResponse({'error': 'Not authorized'}, status=403)

    agent_site = request.user.agent_site

    # Розширений список різноманітних зображень
    image_urls = [
        "https://picsum.photos/id/10/1200/400",
        "https://picsum.photos/id/11/1200/400",
        "https://picsum.photos/id/12/1200/400",
        "https://picsum.photos/id/15/1200/400",
        "https://picsum.photos/id/22/1200/400",
        "https://picsum.photos/id/29/1200/400",
        "https://picsum.photos/id/31/1200/400",
        "https://picsum.photos/id/39/1200/400",
        "https://picsum.photos/id/42/1200/400",
        "https://picsum.photos/id/55/1200/400",
        "https://picsum.photos/id/66/1200/400",
        "https://picsum.photos/id/77/1200/400",
        "https://picsum.photos/id/88/1200/400",
        "https://picsum.photos/id/96/1200/400",
        "https://picsum.photos/id/99/1200/400",
        "https://picsum.photos/id/100/1200/400",
        "https://picsum.photos/id/101/1200/400",
        "https://picsum.photos/id/104/1200/400",
        "https://picsum.photos/id/106/1200/400",
        "https://picsum.photos/id/116/1200/400",
        "https://picsum.photos/id/119/1200/400",
        "https://picsum.photos/id/20/1200/400",
        "https://picsum.photos/id/21/1200/400",
        "https://picsum.photos/id/30/1200/400",
        "https://picsum.photos/id/33/1200/400",
        "https://picsum.photos/id/37/1200/400",
        "https://picsum.photos/id/38/1200/400",
        "https://picsum.photos/id/24/1200/400",
        "https://picsum.photos/id/26/1200/400",
        "https://picsum.photos/id/27/1200/400",
        "https://picsum.photos/id/28/1200/400",
        "https://picsum.photos/id/32/1200/400",
        "https://picsum.photos/id/44/1200/400",
        "https://picsum.photos/id/47/1200/400",
        "https://picsum.photos/id/50/1200/400",
        "https://picsum.photos/id/51/1200/400",
        "https://picsum.photos/id/18/1200/400",
        "https://picsum.photos/id/23/1200/400",
        "https://picsum.photos/id/34/1200/400",
        "https://picsum.photos/id/35/1200/400",
        "https://picsum.photos/id/36/1200/400",
        "https://picsum.photos/id/40/1200/400",
        "https://picsum.photos/id/41/1200/400",
        "https://picsum.photos/id/43/1200/400",
        "https://picsum.photos/id/45/1200/400",
        "https://picsum.photos/id/48/1200/400",
        "https://picsum.photos/id/52/1200/400",
        "https://picsum.photos/id/53/1200/400",
        "https://picsum.photos/id/54/1200/400",
        "https://picsum.photos/id/56/1200/400",
        "https://picsum.photos/id/57/1200/400",
        "https://picsum.photos/id/58/1200/400",
        "https://picsum.photos/id/59/1200/400",
        "https://picsum.photos/id/60/1200/400",
        "https://picsum.photos/id/61/1200/400",
        "https://picsum.photos/id/62/1200/400",
        "https://picsum.photos/id/63/1200/400",
        "https://picsum.photos/id/64/1200/400",
        "https://picsum.photos/id/65/1200/400",
        "https://picsum.photos/id/67/1200/400",
        "https://picsum.photos/id/68/1200/400",
        "https://picsum.photos/id/69/1200/400",
        "https://picsum.photos/id/70/1200/400",
        "https://picsum.photos/id/71/1200/400",
        "https://picsum.photos/id/72/1200/400",
        "https://picsum.photos/id/73/1200/400",
        "https://picsum.photos/id/74/1200/400",
        "https://picsum.photos/id/75/1200/400",
        "https://picsum.photos/id/76/1200/400",
        "https://picsum.photos/id/78/1200/400",
        "https://picsum.photos/id/79/1200/400",
        "https://picsum.photos/id/80/1200/400",
        "https://picsum.photos/id/81/1200/400",
        "https://picsum.photos/id/82/1200/400",
        "https://picsum.photos/id/83/1200/400",
        "https://picsum.photos/id/84/1200/400",
        "https://picsum.photos/id/85/1200/400",
        "https://picsum.photos/id/86/1200/400",
        "https://picsum.photos/id/87/1200/400",
        "https://picsum.photos/id/89/1200/400",
        "https://picsum.photos/id/90/1200/400",
        "https://picsum.photos/id/91/1200/400",
        "https://picsum.photos/id/92/1200/400",
        "https://picsum.photos/id/93/1200/400",
        "https://picsum.photos/id/94/1200/400",
        "https://picsum.photos/id/95/1200/400",
        "https://picsum.photos/id/97/1200/400",
        "https://picsum.photos/id/98/1200/400",
    ]

    random_image_url = random.choice(image_urls)

    try:
        print(f"Генеруємо зображення з URL: {random_image_url}")
        response = requests.get(random_image_url, timeout=30)

        if response.status_code == 200:
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
            agent_site.save()

            messages.success(request, 'Фонове зображення згенеровано та збережено на Cloudinary!')
            return redirect('constructor:dashboard')
        else:
            messages.error(request, 'Не вдалося завантажити зображення. Спробуйте ще раз.')

    except requests.exceptions.Timeout:
        messages.error(request, 'Час очікування минув. Спробуйте ще раз.')
    except Exception as e:
        print(f"Помилка: {e}")
        messages.error(request, f'Помилка: {str(e)[:100]}')

    return redirect('constructor:dashboard')


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

                send_mail(
                    subject='Код для входу в кабінет',
                    message=f'Ваш код для входу: {code}\n\nКод дійсний 10 хвилин.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, 'Код надіслано на ваш email!')
                request.session['code_sent'] = True
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
                    return redirect('agent_home', slug=slug)
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
    Перенаправляє агента на сторінку входу його сайту.
    """
    print("=== agent_login_redirect: Початок ===")

    if request.user.is_authenticated and hasattr(request.user, 'agent_site'):
        slug = request.user.agent_site.slug
        print(f"=== agent_login_redirect: Користувач вже авторизований, перенаправляємо на /a/{slug}/login/ ===")
        return redirect(f'/a/{slug}/login/')

    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"=== agent_login_redirect: Отримано POST з email: {email} ===")

        from users.models import User

        user = User.objects.filter(email=email, is_agent=True).first()
        if not user:
            user = User.objects.filter(username=email, is_agent=True).first()
            print(f"=== agent_login_redirect: Пошук за username, знайдено: {user} ===")

        if user and hasattr(user, 'agent_site'):
            slug = user.agent_site.slug
            print(f"=== agent_login_redirect: Знайдено агента {user}, slug={slug}. Перенаправляємо на /a/{slug}/login/ ===")
            return redirect(f'/a/{slug}/login/')
        else:
            print(f"=== agent_login_redirect: Користувача з email {email} не знайдено або він не є агентом ===")
            messages.error(request, 'Сайт з таким email не знайдено. Перевірте email або зареєструйтесь.')
            return render(request, 'constructor/agent_login_redirect.html')

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
    if not hasattr(request, 'current_agent_site') or not request.current_agent_site:
        raise Http404("Сайт не знайдено")

    from .models.blocks import AgentBlockSettings
    block_settings = AgentBlockSettings.objects.filter(agent=request.current_agent_site.user).first()

    if block_settings:
        request.blocks_order = block_settings.blocks_order
        request.banners = block_settings.banners
        request.active_blocks = block_settings.active_blocks
        request.custom_css = block_settings.custom_css
        request.custom_js = block_settings.custom_js
    else:
        request.blocks_order = AgentBlockSettings().get_default_order()
        request.banners = []
        request.active_blocks = AgentBlockSettings().get_default_order()
        request.custom_css = ''
        request.custom_js = ''

    view_name = request.resolver_match.view_name

    if view_name == 'agent_home':
        return TourListView.as_view()(request)
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
        return ConsultationCreateView.as_view()(request)
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
# ========== НОВІ ФУНКЦІЇ ДЛЯ НАЛАШТУВАНЬ БЛОКІВ ==========
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
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                upload_result = cloudinary.uploader.upload(
                    output,
                    folder=f"agent_{request.user.id}_banners",
                    transformation=[{'quality': 'auto', 'fetch_format': 'auto'}, {'width': 1200, 'crop': 'limit'}]
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


# ========== КІНЕЦЬ НОВИХ ФУНКЦІЙ ==========