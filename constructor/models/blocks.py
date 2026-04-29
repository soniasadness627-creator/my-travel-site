from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AgentBlockSettings(models.Model):
    """Налаштування порядку блоків для агента"""

    MOVABLE_BLOCK_CHOICES = [
        ('price_calendar', '📅 Календар низьких цін'),
        ('recommended_tours', '⭐ Рекомендовані для вас'),
        ('consultation', '📞 Довірте вибір спеціалістам'),
        ('popular_hotels', '🏨 Популярні готелі'),
        ('about_us', 'ℹ️ Про нас'),
        ('popular_destinations', '🌍 Популярні напрямки'),
        ('tours_from_city', '🏙️ Тури з вашого міста'),
        ('banners', '🎯 Мої банери'),
    ]

    POSITION_CHOICES = [
        ('full', 'На всю ширину'),
        ('left', 'Зліва'),
        ('center', 'По центру'),
        ('right', 'Справа'),
    ]

    # ========== ПОЗИЦІЇ ДЛЯ ТЕКСТУ НА БАНЕРІ ==========
    TEXT_POSITION_CHOICES = [
        ('top-left', 'Вгорі зліва'),
        ('top-center', 'Вгорі по центру'),
        ('top-right', 'Вгорі справа'),
        ('center-left', 'По центру зліва'),
        ('center', 'По центру'),
        ('center-right', 'По центру справа'),
        ('bottom-left', 'Внизу зліва'),
        ('bottom-center', 'Внизу по центру'),
        ('bottom-right', 'Внизу справа'),
    ]

    agent = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='block_settings',
        limit_choices_to={'is_agent': True}
    )

    blocks_order = models.JSONField(default=list)
    active_blocks = models.JSONField(default=list)

    # ОНОВЛЕНА СТРУКТУРА БАНЕРІВ - з підтримкою кількох текстових блоків
    banners = models.JSONField(
        default=list,
        help_text=(
            "[{"
            "'image': 'url', "
            "'link': 'url', "
            "'position': 'full', "
            "'title': 'Назва банера', "
            "'order': 1, "
            "'active': True, "
            "'overlay_opacity': 0.4, "
            "'text_blocks': ["
            "{"
            "'id': '1', "
            "'heading': 'Заголовок', "
            "'text': 'Текст', "
            "'position': 'center', "
            "'heading_color': '#ffffff', "
            "'text_color': '#ffffff', "
            "'button_text': 'Детальніше', "
            "'button_color': '#086745', "
            "'button_link': 'https://...'"
            "}"
            "]"
            "}]"
        )
    )

    custom_css = models.TextField(blank=True)
    custom_js = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Налаштування блоків агента"
        verbose_name_plural = "Налаштування блоків агентів"

    def __str__(self):
        return f"Блоки агента {self.agent.username}"

    def get_default_order(self):
        return [
            'price_calendar',
            'recommended_tours',
            'consultation',
            'popular_hotels',
            'about_us',
            'popular_destinations',
            'tours_from_city',
            'banners',
        ]