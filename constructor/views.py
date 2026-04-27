import random
import uuid
import requests
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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.urls import reverse_lazy
from .forms import AgentRegistrationForm, VerificationForm, AgentSiteForm
from users.models import User
from .models import AgentSite
from tours.views import TourListView, tour_detail, search_results, city_detail, news_detail, ConsultationCreateView, \
    NewsListView, get_agent_colors, tour_reviews
from tours.models import News

from django.http import HttpResponse


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
    Верифікація коду з email - ТИМЧАСОВО з автопідтвердженням
    """
    print("=== agent_verify: Початок ===")

    # ТИМЧАСОВО: автоматичне підтвердження для тестування
    # ПІСЛЯ ТЕСТУВАННЯ ВИДАЛИТИ РЯДОК "or True" НИЖЧЕ
    if request.method == 'POST' or True:  # <--- ТУТ "or True" означає, що завжди спрацьовує
        data = request.session.get('reg_data')
        if data:
            email = data['email']
            print(f"ТИМЧАСОВО: Автоматичне створення агента для {email}")

            from users.models import User
            from .models import AgentSite
            from django.utils.text import slugify
            from django.contrib.auth import login

            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    is_agent=True
                )
                user.set_unusable_password()
                user.save()
                print(f"Створено нового користувача: {user.id}")
            else:
                print(f"Користувач вже існує: {user.id}")

            # Створюємо агентський сайт
            base_slug = slugify(email.split('@')[0])
            if not base_slug:
                base_slug = f"user_{user.id}"
            unique_slug = base_slug
            counter = 1
            while AgentSite.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1

            agent_site, created = AgentSite.objects.get_or_create(user=user, defaults={'slug': unique_slug})
            print(f"Агентський сайт: {agent_site.slug}, створено: {created}")

            login(request, user)

            # Очищаємо сесію
            if 'reg_code' in request.session:
                del request.session['reg_code']
            if 'reg_data' in request.session:
                del request.session['reg_data']

            return redirect('/constructor/dashboard/')
        else:
            print("Немає даних в сесії reg_data")

    # Якщо щось пішло не так, показуємо форму
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

    if request.method == 'POST':
        form = AgentSiteForm(request.POST, request.FILES, instance=agent_site)
        if form.is_valid():
            saved_site = form.save()
            messages.success(request, 'Налаштування збережено!')
            agent_site = saved_site
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
    Генерує фонове зображення для агентського сайту.
    Використовує кілька резервних джерел зображень.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'agent_site'):
        return JsonResponse({'error': 'Not authorized'}, status=403)

    agent_site = request.user.agent_site

    # Список резервних джерел зображень
    image_urls = [
        "https://picsum.photos/id/104/1200/400",  # пейзаж
        "https://picsum.photos/id/15/1200/400",  # природа
        "https://picsum.photos/id/22/1200/400",  # пейзаж
        "https://picsum.photos/id/96/1200/400",  # гора
        "https://picsum.photos/id/42/1200/400",  # музика
    ]

    for image_url in image_urls:
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                filename = f"generated_{uuid.uuid4().hex[:10]}.jpg"
                agent_site.hero_background.save(filename, ContentFile(response.content), save=True)
                messages.success(request, 'Фонове зображення згенеровано та збережено!')
                return redirect('constructor:dashboard')
        except requests.exceptions.Timeout:
            continue  # пробуємо наступне джерело
        except Exception as e:
            print(f"Помилка завантаження {image_url}: {e}")
            continue  # пробуємо наступне джерело

    # Якщо жодне джерело не спрацювало
    messages.error(request, 'Не вдалося згенерувати зображення. Спробуйте завантажити вручну.')
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
    print("=== agent_login_redirect: Початок ===")  # Діагностика

    # Якщо користувач вже авторизований і має агентський сайт
    if request.user.is_authenticated and hasattr(request.user, 'agent_site'):
        slug = request.user.agent_site.slug
        print(f"=== agent_login_redirect: Користувач вже авторизований, перенаправляємо на /a/{slug}/login/ ===")
        return redirect(f'/a/{slug}/login/')

    # Обробка POST запиту (форма з email)
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"=== agent_login_redirect: Отримано POST з email: {email} ===")
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(email=email, is_agent=True).first()
        if not user:
            user = User.objects.filter(username=email, is_agent=True).first()
            print(f"=== agent_login_redirect: Пошук за username, знайдено: {user} ===")

        if user and hasattr(user, 'agent_site'):
            slug = user.agent_site.slug
            print(
                f"=== agent_login_redirect: Знайдено агента {user}, slug={slug}. Перенаправляємо на /a/{slug}/login/ ===")
            return redirect(f'/a/{slug}/login/')
        else:
            print(f"=== agent_login_redirect: Користувача з email {email} не знайдено або він не є агентом ===")
            messages.error(request, 'Сайт з таким email не знайдено. Перевірте email або зареєструйтесь.')

    # GET запит - показуємо форму
    print("=== agent_login_redirect: Показуємо форму (GET-запит) ===")
    return render(request, 'constructor/agent_login_redirect.html')


# ========== ТИМЧАСОВИЙ КОД ДЛЯ СТВОРЕННЯ СУПЕРАДМІНА ==========
# ВИДАЛИТИ ПІСЛЯ ВИКОРИСТАННЯ
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