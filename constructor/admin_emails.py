from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model
import requests
import csv
import io

User = get_user_model()


class MassEmailAdmin(admin.AdminSite):
    """Розширена адмінка з можливістю масової розсилки"""

    site_header = "Адмін-панель TourConstructor"
    site_title = "TourConstructor Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mass-email/', self.admin_view(self.mass_email_view), name='mass-email'),
            path('send-mass-email/', self.admin_view(self.send_mass_email), name='send-mass-email'),
        ]
        return custom_urls + urls

    def mass_email_view(self, request):
        """Сторінка для створення розсилки"""
        if not request.user.is_superuser:
            messages.error(request, "Доступ тільки для суперадміна")
            return redirect('/admin/')

        agents_count = User.objects.filter(is_agent=True).count()
        agents = User.objects.filter(is_agent=True).values_list('email', 'username')[:20]

        context = {
            'agents_count': agents_count,
            'agents_preview': agents,
            'title': 'Масова email-розсилка'
        }
        return render(request, 'admin/mass_email.html', context)

    def send_mass_email(self, request):
        """Відправка листів через Mailgun"""
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Access denied'}, status=403)

        if request.method == 'POST':
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            recipient_type = request.POST.get('recipient_type', 'all_agents')
            uploaded_file = request.FILES.get('email_file')

            emails = []

            if recipient_type == 'all_agents':
                emails = list(User.objects.filter(is_agent=True, email__isnull=False)
                              .exclude(email='')
                              .values_list('email', flat=True))
            elif recipient_type == 'upload_file' and uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                if uploaded_file.name.endswith('.csv'):
                    reader = csv.reader(io.StringIO(content))
                    for row in reader:
                        if row and '@' in row[0]:
                            emails.append(row[0].strip())
                else:
                    for line in content.splitlines():
                        if '@' in line:
                            emails.append(line.strip())

            if not emails:
                messages.error(request, 'Не знайдено email для розсилки')
                return redirect('admin:mass-email')

            success_count = 0
            fail_count = 0

            for email in emails[:50]:
                result = self.send_via_mailgun(email, subject, message)
                if result:
                    success_count += 1
                else:
                    fail_count += 1

            messages.success(
                request,
                f'Розсилку розпочато! Відправлено {success_count} листів, помилок: {fail_count}'
            )

            if len(emails) > 50:
                messages.warning(
                    request,
                    f'Для відправки {len(emails)} листів рекомендується використовувати фоновий процес'
                )

            return redirect('admin:mass-email')

        return redirect('admin:mass-email')

    def send_via_mailgun(self, to_email, subject, message):
        """Відправка через Mailgun API"""
        if not settings.MAILGUN_API_KEY:
            return False

        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data={
                    "from": settings.MAILGUN_FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": message.replace('\n', '<br>')
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Помилка Mailgun: {e}")
            return False


# Створюємо екземпляр
mass_email_admin = MassEmailAdmin(name='mass_email_admin')