from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator

User = get_user_model()


class AgentSite(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_site')
    slug = models.SlugField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(3), RegexValidator(r'^[a-z0-9-]+$', 'Лише малі літери, цифри та дефіс')],
        verbose_name="Адреса сайту"
    )
    agency_name = models.CharField(max_length=200, blank=True, verbose_name="Назва турагенції")
    hero_title = models.CharField(max_length=200, default="Ваша подорож починається тут")
    hero_subtitle = models.CharField(max_length=200, default="Знайдіть ідеальний тур за лічені хвилини")
    hero_background = models.ImageField(upload_to='agent_hero/', blank=True, null=True,
                                        verbose_name="Фонова картинка (рекомендовано 1200x400px)")
    top_logo = models.ImageField(upload_to='agent_logos/', blank=True, null=True,
                                 verbose_name="Верхній логотип (250x250px)")
    bottom_logo = models.ImageField(upload_to='agent_logos/', blank=True, null=True,
                                    verbose_name="Нижній логотип (150x150px або 150x50px)")
    enlarge_logo = models.BooleanField(default=False, verbose_name="Збільшити логотип на 25%")
    show_news = models.BooleanField(default=True, verbose_name="Показувати новини")
    show_operator_logos = models.BooleanField(default=False,
                                              verbose_name="Відображати логотипи туроператорів на сайті при пошуку турів")
    show_superadmin_tours = models.BooleanField(default=False, verbose_name="Показувати тури суперадміна")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Кольорова схема
    primary_color = models.CharField(
        max_length=7,
        default="#086745",
        verbose_name="Головний колір",
        help_text="Колір для кнопок, посилань та акцентів. Введіть HEX-код, наприклад #086745"
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#02432c",
        verbose_name="Додатковий колір",
        help_text="Колір для hover-ефектів. Введіть HEX-код, наприклад #02432c"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.slug}"

    def get_primary_color(self):
        """Повертає головний колір або значення за замовчуванням"""
        return self.primary_color or "#086745"

    def get_secondary_color(self):
        """Повертає додатковий колір або значення за замовчуванням"""
        return self.secondary_color or "#02432c"

    def get_primary_light(self):
        """Повертає світлішу версію головного кольору (для фонів)"""
        primary = self.get_primary_color()
        # Конвертуємо HEX в RGB і робимо світлішим
        try:
            r = int(primary[1:3], 16)
            g = int(primary[3:5], 16)
            b = int(primary[5:7], 16)
            # Робимо колір світлішим (додаємо 100 до кожного компонента, але не більше 255)
            r = min(r + 100, 255)
            g = min(g + 100, 255)
            b = min(b + 100, 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#cbf6ec"

    def get_primary_lighter(self):
        """Повертає дуже світлу версію головного кольору (для фонів)"""
        primary = self.get_primary_color()
        try:
            r = int(primary[1:3], 16)
            g = int(primary[3:5], 16)
            b = int(primary[5:7], 16)
            # Робимо колір дуже світлим (додаємо 180 до кожного компонента, але не більше 255)
            r = min(r + 180, 255)
            g = min(g + 180, 255)
            b = min(b + 180, 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#cbf6ec"

    def get_contrast_color(self):
        """Повертає білий або чорний колір залежно від яскравості головного кольору"""
        primary = self.get_primary_color()
        try:
            r = int(primary[1:3], 16)
            g = int(primary[3:5], 16)
            b = int(primary[5:7], 16)
            # Обчислюємо яскравість (формула Y = 0.299R + 0.587G + 0.114B)
            brightness = (r * 0.299 + g * 0.587 + b * 0.114)
            return "#ffffff" if brightness < 128 else "#000000"
        except:
            return "#ffffff"