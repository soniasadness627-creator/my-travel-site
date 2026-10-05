from django import forms
from ..models.agent_site import AgentSite


class AgentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30, label="Ім'я", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, label="Прізвище", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))


class VerificationForm(forms.Form):
    code = forms.CharField(
        label='Код верифікації',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Введіть 6-значний код',
            'pattern': '[0-9]{6}',
            'autocomplete': 'off'
        })
    )


class AgentSiteForm(forms.ModelForm):
    # ========== ПОЛЕ ДЛЯ МЕНЕДЖЕРІВ (JSON) ==========
    managers = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_managers_json'})
    )

    class Meta:
        model = AgentSite
        fields = [
            'slug', 'agency_name', 'hero_title', 'hero_subtitle', 'hero_background',
            'top_logo', 'bottom_logo', 'enlarge_logo', 'show_news', 'show_operator_logos',
            'primary_color', 'secondary_color',
            'about_us_title', 'about_us_text', 'about_us_image',
            'favicon',
            'hide_logo',
            # ========== СОЦІАЛЬНІ МЕРЕЖІ (ОСНОВНІ) ==========
            'social_youtube', 'social_tiktok', 'social_instagram',
            'social_facebook', 'social_telegram',
            # ========== СОЦІАЛЬНІ МЕРЕЖІ (ДОДАТКОВІ) ==========
            'social_whatsapp', 'social_viber', 'social_threads',
            'social_linkedin', 'social_x', 'social_pinterest',
            'social_snapchat', 'social_twitch', 'social_discord',
            'social_signal',
            # ========== МЕНЕДЖЕРИ (JSON) ==========
            'managers',
            # ========== КОНТАКТНА ІНФОРМАЦІЯ ДЛЯ ФУТЕРА ==========
            'footer_phone', 'footer_address', 'footer_email', 'footer_show_contact',
            # ========== TELEGRAM СПОВІЩЕННЯ ==========
            'telegram_chat_id',
        ]
        widgets = {
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'назва-агенції'
            }),
            'agency_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'hero_title': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'hero_subtitle': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'hero_background': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'top_logo': forms.ClearableFileInput(attrs={
                'accept': 'image/png,image/svg+xml',
                'class': 'form-control'
            }),
            'bottom_logo': forms.ClearableFileInput(attrs={
                'accept': 'image/png,image/svg+xml',
                'class': 'form-control'
            }),
            'enlarge_logo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_news': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_operator_logos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'style': 'width: 60px; height: 38px; padding: 0;'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'style': 'width: 60px; height: 38px; padding: 0;'
            }),
            # ВІДЖЕТИ ДЛЯ БЛОКУ "ПРО НАС"
            'about_us_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть заголовок блоку'
            }),
            'about_us_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Розкажіть про вашу компанію...'
            }),
            'about_us_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            # FAVICON
            'favicon': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/png,image/svg+xml,image/x-icon,image/vnd.microsoft.icon'
            }),
            # HIDE_LOGO
            'hide_logo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            # ========== СОЦІАЛЬНІ МЕРЕЖІ (ОСНОВНІ) ==========
            'social_youtube': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/...'
            }),
            'social_tiktok': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/...'
            }),
            'social_instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/...'
            }),
            'social_facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/...'
            }),
            'social_telegram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://t.me/...'
            }),
            # ========== СОЦІАЛЬНІ МЕРЕЖІ (ДОДАТКОВІ) ==========
            'social_whatsapp': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://wa.me/380991234567'
            }),
            'social_viber': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'viber://chat?number=380991234567'
            }),
            'social_threads': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://threads.net/@username'
            }),
            'social_linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'social_x': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://x.com/username'
            }),
            'social_pinterest': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://pinterest.com/username'
            }),
            'social_snapchat': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://snapchat.com/add/username'
            }),
            'social_twitch': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitch.tv/username'
            }),
            'social_discord': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://discord.gg/invite'
            }),
            'social_signal': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://signal.me/#p/...'
            }),
            # ========== КОНТАКТНА ІНФОРМАЦІЯ ДЛЯ ФУТЕРА ==========
            'footer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+38 (099) 123-45-67'
            }),
            'footer_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'м. Київ, вул. Хрещатик, 1'
            }),
            'footer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'info@clubdatour.com.ua'
            }),
            'footer_show_contact': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            # ========== TELEGRAM СПОВІЩЕННЯ ==========
            'telegram_chat_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: 123456789 (отримайте у @userinfobot)'
            }),
        }
        labels = {
            'slug': 'Адреса сайту (slug)',
            'agency_name': 'Назва турагенції',
            'hero_title': 'Заголовок головної секції',
            'hero_subtitle': 'Підзаголовок головної секції',
            'hero_background': 'Фонове зображення',
            'top_logo': 'Верхній логотип',
            'bottom_logo': 'Нижній логотип',
            'enlarge_logo': 'Збільшити логотип на 25%',
            'show_news': 'Показувати новини',
            'show_operator_logos': 'Показувати логотипи туроператорів',
            'primary_color': 'Головний колір',
            'secondary_color': 'Додатковий колір (hover)',
            # ЛЕЙБЛИ ДЛЯ БЛОКУ "ПРО НАС"
            'about_us_title': 'Заголовок блоку "Про нас"',
            'about_us_text': 'Текст блоку "Про нас"',
            'about_us_image': 'Фото для блоку "Про нас"',
            # FAVICON
            'favicon': 'Іконка сайту (favicon)',
            # HIDE_LOGO
            'hide_logo': 'Без логотипу (немає логотипу)',
            # ========== СОЦІАЛЬНІ МЕРЕЖІ ==========
            'social_youtube': 'YouTube',
            'social_tiktok': 'TikTok',
            'social_instagram': 'Instagram',
            'social_facebook': 'Facebook',
            'social_telegram': 'Telegram',
            'social_whatsapp': 'WhatsApp',
            'social_viber': 'Viber',
            'social_threads': 'Threads',
            'social_linkedin': 'LinkedIn',
            'social_x': 'X (Twitter)',
            'social_pinterest': 'Pinterest',
            'social_snapchat': 'Snapchat',
            'social_twitch': 'Twitch',
            'social_discord': 'Discord',
            'social_signal': 'Signal',
            # ========== МЕНЕДЖЕРИ ==========
            'managers': 'Менеджери',
            # ========== КОНТАКТНА ІНФОРМАЦІЯ ДЛЯ ФУТЕРА ==========
            'footer_phone': 'Телефон у футері',
            'footer_address': 'Адреса офісу у футері',
            'footer_email': 'Email у футері',
            'footer_show_contact': 'Показувати контакти у футері',
            # ========== TELEGRAM СПОВІЩЕННЯ ==========
            'telegram_chat_id': 'Telegram Chat ID для сповіщень',
        }
        help_texts = {
            'slug': 'Унікальна адреса вашого сайту (латиниця, дефіси)',
            'hero_background': 'Рекомендований розмір: 1200×400px',
            'top_logo': 'Формати: PNG, SVG. Рекомендований розмір: 250×250px',
            'bottom_logo': 'Формати: PNG, SVG. Рекомендований розмір: 150×150px або 150×50px',
            'primary_color': 'Колір для кнопок, посилань та акцентів',
            'secondary_color': 'Колір для hover-ефектів',
            # ПІДКАЗКИ ДЛЯ БЛОКУ "ПРО НАС"
            'about_us_text': 'Розкажіть клієнтам про вашу компанію, ваш досвід та переваги',
            'about_us_image': 'Рекомендований розмір: 800×600px. Формати: JPG, PNG',
            # FAVICON
            'favicon': 'Іконка, яка відображається у вкладці браузера. Рекомендований розмір: 32×32px, 64×64px або 128×128px. Формати: PNG, ICO, SVG, GIF',
            # HIDE_LOGO
            'hide_logo': 'Якщо увімкнути, логотип не відображатиметься на сайті (ні свій, ні наш)',
            # ========== СОЦІАЛЬНІ МЕРЕЖІ ==========
            'social_youtube': 'Вставте повне посилання на ваш YouTube канал',
            'social_tiktok': 'Вставте повне посилання на ваш TikTok',
            'social_instagram': 'Вставте повне посилання на ваш Instagram',
            'social_facebook': 'Вставте повне посилання на вашу Facebook сторінку',
            'social_telegram': 'Вставте повне посилання на ваш Telegram канал або чат',
            'social_whatsapp': 'Посилання на WhatsApp (наприклад: https://wa.me/380991234567)',
            'social_viber': 'Посилання на Viber (наприклад: viber://chat?number=380991234567)',
            'social_threads': 'Вставте повне посилання на ваш Threads',
            'social_linkedin': 'Вставте повне посилання на ваш LinkedIn',
            'social_x': 'Вставте повне посилання на ваш X/Twitter',
            'social_pinterest': 'Вставте повне посилання на ваш Pinterest',
            'social_snapchat': 'Вставте повне посилання на ваш Snapchat',
            'social_twitch': 'Вставте повне посилання на ваш Twitch',
            'social_discord': 'Вставте повне посилання на ваш Discord',
            'social_signal': 'Вставте повне посилання на ваш Signal',
            # ========== МЕНЕДЖЕРИ ==========
            'managers': 'Додайте одного або декількох менеджерів',
            # ========== КОНТАКТНА ІНФОРМАЦІЯ ДЛЯ ФУТЕРА ==========
            'footer_phone': 'Номер телефону для відображення у футері (наприклад: +38 (099) 123-45-67)',
            'footer_address': 'Адреса для відображення у футері (наприклад: м. Київ, вул. Хрещатик, 1)',
            'footer_email': 'Email для відображення у футері',
            'footer_show_contact': 'Відображати блок з контактною інформацією у футері',
            # ========== TELEGRAM СПОВІЩЕННЯ ==========
            'telegram_chat_id': 'Отримайте ваш Chat ID у бота @userinfobot',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            import re
            if not re.match(r'^[a-zA-Z0-9-]+$', slug):
                raise forms.ValidationError('Slug може містити тільки латинські літери (великі та малі), цифри та дефіс.')
            instance = getattr(self, 'instance', None)
            if instance and instance.pk:
                if AgentSite.objects.exclude(pk=instance.pk).filter(slug=slug).exists():
                    raise forms.ValidationError('Сайт з такою адресою вже існує.')
            else:
                if AgentSite.objects.filter(slug=slug).exists():
                    raise forms.ValidationError('Сайт з такою адресою вже існує.')
        return slug

    def clean_primary_color(self):
        primary_color = self.cleaned_data.get('primary_color')
        if primary_color:
            import re
            if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', primary_color):
                raise forms.ValidationError('Введіть коректний HEX код кольору (наприклад, #086745)')
        return primary_color

    def clean_secondary_color(self):
        secondary_color = self.cleaned_data.get('secondary_color')
        if secondary_color:
            import re
            if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', secondary_color):
                raise forms.ValidationError('Введіть коректний HEX код кольору (наприклад, #02432c)')
        return secondary_color

    def clean_managers(self):
        """Валідація списку менеджерів (JSON вже розпарсений forms.JSONField)"""
        managers = self.cleaned_data.get('managers')
        if not managers or not isinstance(managers, list):
            return []
        cleaned = []
        for m in managers:
            if not isinstance(m, dict):
                continue
            # Залишаємо тільки заповнених (ім'я або телефон)
            if not (m.get('name') or m.get('phone')):
                continue
            cleaned.append({
                'name': (m.get('name') or '').strip(),
                'position': (m.get('position') or '').strip(),
                'phone': (m.get('phone') or '').strip(),
                'email': (m.get('email') or '').strip(),
                'telegram': (m.get('telegram') or '').strip(),
                'whatsapp': (m.get('whatsapp') or '').strip(),
            })
        return cleaned

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('secondary_color') and cleaned_data.get('primary_color'):
            primary = cleaned_data.get('primary_color')
            try:
                r = int(primary[1:3], 16)
                g = int(primary[3:5], 16)
                b = int(primary[5:7], 16)
                r = max(0, int(r * 0.8))
                g = max(0, int(g * 0.8))
                b = max(0, int(b * 0.8))
                cleaned_data['secondary_color'] = f"#{r:02x}{g:02x}{b:02x}"
            except:
                cleaned_data['secondary_color'] = '#02432c'
        return cleaned_data