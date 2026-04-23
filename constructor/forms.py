from django import forms
from .models import AgentSite

class AgentRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30, label="Ім'я", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, label="Прізвище", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))


class VerificationForm(forms.Form):
    code = forms.CharField(max_length=6, label="Код підтвердження", widget=forms.TextInput(attrs={'class': 'form-control'}))


class AgentSiteForm(forms.ModelForm):
    class Meta:
        model = AgentSite
        fields = [
            'slug', 'agency_name', 'hero_title', 'hero_subtitle', 'hero_background',
            'top_logo', 'bottom_logo', 'enlarge_logo', 'show_news', 'show_operator_logos',
            'show_superadmin_tours', 'primary_color', 'secondary_color'
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
            'show_superadmin_tours': forms.CheckboxInput(attrs={
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
            'show_superadmin_tours': 'Показувати тури суперадміна',
            'primary_color': 'Головний колір',
            'secondary_color': 'Додатковий колір (hover)',
        }
        help_texts = {
            'slug': 'Унікальна адреса вашого сайту (тільки латиниця, дефіси)',
            'hero_background': 'Рекомендований розмір: 1200×400px',
            'top_logo': 'Формати: PNG, SVG. Рекомендований розмір: 250×250px',
            'bottom_logo': 'Формати: PNG, SVG. Рекомендований розмір: 150×150px або 150×50px',
            'primary_color': 'Колір для кнопок, посилань та акцентів',
            'secondary_color': 'Колір для hover-ефектів',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            # Перевіряємо, що slug містить тільки дозволені символи
            import re
            if not re.match(r'^[a-z0-9-]+$', slug):
                raise forms.ValidationError('Slug може містити тільки малі латинські літери, цифри та дефіс.')
            # Перевіряємо унікальність, ігноруючи поточний об'єкт
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
            # Перевіряємо формат HEX кольору
            import re
            if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', primary_color):
                raise forms.ValidationError('Введіть коректний HEX код кольору (наприклад, #086745)')
        return primary_color

    def clean_secondary_color(self):
        secondary_color = self.cleaned_data.get('secondary_color')
        if secondary_color:
            # Перевіряємо формат HEX кольору
            import re
            if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', secondary_color):
                raise forms.ValidationError('Введіть коректний HEX код кольору (наприклад, #02432c)')
        return secondary_color

    def clean(self):
        cleaned_data = super().clean()
        # Якщо вторинний колір не вказаний, використовуємо затемнену версію основного
        if not cleaned_data.get('secondary_color') and cleaned_data.get('primary_color'):
            primary = cleaned_data.get('primary_color')
            # Затемнюємо основний колір для hover-ефекту
            try:
                r = int(primary[1:3], 16)
                g = int(primary[3:5], 16)
                b = int(primary[5:7], 16)
                # Затемнюємо на 20%
                r = max(0, int(r * 0.8))
                g = max(0, int(g * 0.8))
                b = max(0, int(b * 0.8))
                cleaned_data['secondary_color'] = f"#{r:02x}{g:02x}{b:02x}"
            except:
                cleaned_data['secondary_color'] = '#02432c'
        return cleaned_data