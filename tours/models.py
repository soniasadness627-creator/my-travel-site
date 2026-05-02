from django.db import models
from django.conf import settings
from smart_selects.db_fields import ChainedForeignKey
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()


class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва міста")
    country = models.CharField(max_length=100, verbose_name="Країна")
    description = models.TextField(blank=True, verbose_name="Основна інформація про місто")
    activities = models.TextField(blank=True, verbose_name="Чим зайнятися на курорті?")
    sights = models.TextField(blank=True, verbose_name="Найцікавіші визначні місця")

    class Meta:
        verbose_name = "Місто"
        verbose_name_plural = "Міста"
        ordering = ['country', 'name']

    def __str__(self):
        return f"{self.name} ({self.country})"


class DepartureCity(models.Model):
    TRANSPORT_CHOICES = [
        ('air', 'літак'),
        ('bus', 'автобус'),
    ]
    name = models.CharField(max_length=100, verbose_name="Місто вильоту")
    country = models.CharField(max_length=100, verbose_name="Країна")
    transport = models.CharField(max_length=50, choices=TRANSPORT_CHOICES, verbose_name="Транспорт")

    class Meta:
        verbose_name = "Місто вильоту"
        verbose_name_plural = "Міста вильоту"
        ordering = ['country', 'name']

    def __str__(self):
        return f"{self.name} ({self.country}, {self.get_transport_display()})"


class Tour(models.Model):
    title = models.CharField(max_length=200, verbose_name="Назва туру")
    description = models.TextField(verbose_name="Опис")
    country = models.CharField(max_length=100, verbose_name="Країна")
    city = ChainedForeignKey(
        City,
        chained_field="country",
        chained_model_field="country",
        show_all=False,
        auto_choose=True,
        sort=True,
        blank=True,
        null=True,
        verbose_name="Курорт/місто"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    STARS_CHOICES = [
        (1, '1*'),
        (2, '2*'),
        (3, '3*'),
        (4, '4*'),
        (5, '5*'),
    ]

    stars = models.IntegerField(
        verbose_name="Категорія готелю (зірки)",
        choices=STARS_CHOICES,
        null=True,
        blank=True,
        default=None,
        help_text="Виберіть категорію готелю"
    )
    start_date = models.DateField(verbose_name="Дата початку")
    end_date = models.DateField(verbose_name="Дата закінчення")
    image = CloudinaryField(verbose_name="Фото туру", folder='tours', blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tours'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    map_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Посилання на карту",
        help_text="Вставте посилання на Google Maps (iframe src)"
    )

    amenities = models.ManyToManyField(
        'Amenity',
        blank=True,
        related_name='tours',
        verbose_name="Послуги та зручності"
    )

    departure_city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Місто виїзду"
    )

    TRANSPORT_CHOICES = [
        ('air', 'літак'),
        ('bus', 'автобус'),
    ]
    transport = models.CharField(
        max_length=10,
        choices=TRANSPORT_CHOICES,
        default='air',
        verbose_name="Транспорт"
    )

    duration = models.PositiveSmallIntegerField(
        verbose_name="Тривалість (ночей)",
        help_text="Кількість ночей",
        default=1
    )

    room_type = models.CharField(
        max_length=100,
        verbose_name="Тип номера",
        blank=True,
        default="Standard"
    )
    MEAL_CHOICES = [
        ('RO', 'Без харчування'),
        ('BB', 'Сніданок'),
        ('HB', 'Дворазове харчування'),
        ('FB', 'Триразове харчування'),
        ('AI', 'All Inclusive'),
        ('UAI', 'Ultra All Inclusive'),
    ]
    meal_type = models.CharField(
        max_length=3,
        choices=MEAL_CHOICES,
        default='RO',
        verbose_name="Харчування"
    )

    is_popular = models.BooleanField(default=False, verbose_name="Популярний готель")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class PopularDestination(models.Model):
    country = models.CharField(max_length=100, unique=True, verbose_name="Країна")
    image = models.ImageField(upload_to='popular_destinations/', verbose_name="Фото для блоку")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок сортування")

    class Meta:
        verbose_name = "Популярний напрямок"
        verbose_name_plural = "Популярні напрямки"
        ordering = ['order']

    def __str__(self):
        return self.country


class Consultation(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ім'я")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    comment = models.TextField(blank=True, verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заявки")
    is_processed = models.BooleanField(default=False, verbose_name="Опрацьовано")
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Агент",
        related_name="consultations"
    )

    def __str__(self):
        return f"Консультація для {self.name} ({self.phone})"

    class Meta:
        verbose_name = "Заявка на консультацію"
        verbose_name_plural = "Заявки на консультацію"
        ordering = ['-created_at']


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="tour_gallery/", verbose_name="Додаткове фото")

    def __str__(self):
        return f"Фото для {self.tour.title}"


# ========== ВИПРАВЛЕНА МОДЕЛЬ BOOKING (ДОДАНО null=True, blank=True) ==========
class Booking(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,      # ← ДОДАНО
        blank=True      # ← ДОДАНО
    )
    name = models.CharField(max_length=100, verbose_name="Ім'я")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(blank=True, verbose_name="Повідомлення")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.tour:
            return f"Заявка на {self.tour.title} від {self.name}"
        return f"Заявка на тур від {self.name}"

    class Meta:
        verbose_name = "Бронювання"
        verbose_name_plural = "Бронювання"
        ordering = ['-created_at']


class Review(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Ваше ім'я")
    rating = models.PositiveSmallIntegerField(
        verbose_name="Оцінка",
        choices=[(i, i) for i in range(1, 6)],
        help_text="Оцініть тур від 1 до 5"
    )
    comment = models.TextField(verbose_name="Коментар", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Відгук від {self.user.username} на {self.tour}"
        return f"Відгук від {self.guest_name} на {self.tour}"

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        ordering = ['-created_at']


class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст")
    image = models.ImageField(upload_to="news/", blank=True, null=True, verbose_name="Головне фото")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Автор",
        related_name="news"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ['-created_at']


class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='news_gallery/', verbose_name="Додаткове фото")

    def __str__(self):
        return f"Фото для {self.news.title}"


class PriceOption(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='price_options', verbose_name="Тур")
    departure_date = models.DateField(verbose_name="Дата вильоту", null=True, blank=True)
    duration = models.PositiveSmallIntegerField(
        verbose_name="Тривалість (ночей)",
        help_text="Кількість ночей",
        null=True,
        blank=True
    )
    departure_city = models.CharField(
        max_length=100,
        default='Кишинів',
        verbose_name="Місто вильоту",
        blank=True
    )
    room_type = models.CharField(
        max_length=100,
        verbose_name="Тип номера",
        blank=True,
        default="Standard"
    )
    meal_type = models.CharField(
        max_length=50,
        verbose_name="Харчування",
        choices=[
            ('RO', 'Без харчування'),
            ('BB', 'Сніданок'),
            ('HB', 'Напівпансіон'),
            ('FB', 'Повний пансіон'),
            ('AI', 'Все включено'),
        ],
        default='AI',
        blank=True
    )
    adults = models.PositiveSmallIntegerField(default=2, verbose_name="Кількість дорослих")
    infants = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 0-2 роки (без місця)")
    children_2_3 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 2-3 роки")
    children_4_10 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 4-10 років")
    children_11_16 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 11-16 років")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за тур")
    is_available = models.BooleanField(default=True, verbose_name="Доступно")

    class Meta:
        verbose_name = "Варіант ціни"
        verbose_name_plural = "Варіанти цін"
        ordering = ['departure_date', 'price']
        unique_together = (
            'tour', 'departure_date', 'duration', 'departure_city',
            'room_type', 'meal_type', 'adults', 'infants',
            'children_2_3', 'children_4_10', 'children_11_16'
        )

    def __str__(self):
        return (f"{self.tour.title} – {self.departure_date} ({self.duration} ночей) – {self.price}$ "
                f"(A{self.adults}, I{self.infants}, C2-3{self.children_2_3}, "
                f"C4-10{self.children_4_10}, C11-16{self.children_11_16})")


class CountryInfo(models.Model):
    country = models.CharField(max_length=100, unique=True, verbose_name="Країна")
    main_text = models.TextField(verbose_name="Основна інформація", blank=True)
    why_text = models.TextField(verbose_name="Чому варто вибрати?", blank=True)
    popular_resorts = models.TextField(verbose_name="Популярні курорти", blank=True)
    activities = models.TextField(verbose_name="Доступні види відпочинку", blank=True)
    sights = models.TextField(verbose_name="Основні визначні пам'ятки", blank=True)
    useful_facts = models.TextField(verbose_name="Корисні факти для туристів", blank=True)

    class Meta:
        verbose_name = "Інформація про країну"
        verbose_name_plural = "Інформація про країни"

    def __str__(self):
        return self.country


class TourPriceByTourists(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='prices_by_tourists',
        verbose_name="Тур"
    )
    adults = models.PositiveSmallIntegerField(default=2, verbose_name="Кількість дорослих")
    infants = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 0-2 роки (без місця)")
    children_2_3 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 2-3 роки")
    children_4_10 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 4-10 років")
    children_11_16 = models.PositiveSmallIntegerField(default=0, verbose_name="Діти 11-16 років")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    is_default = models.BooleanField(default=False, verbose_name="Ціна за замовчуванням (якщо немає точної відповідності)")

    class Meta:
        verbose_name = "Ціна за складом туристів"
        verbose_name_plural = "Ціни за складом туристів"
        unique_together = ('tour', 'adults', 'infants', 'children_2_3', 'children_4_10', 'children_11_16')

    def __str__(self):
        parts = [f"{self.adults} дорослих"]
        if self.infants:
            parts.append(f"{self.infants} немовлят (0-2)")
        if self.children_2_3:
            parts.append(f"{self.children_2_3} дітей 2-3р")
        if self.children_4_10:
            parts.append(f"{self.children_4_10} дітей 4-10р")
        if self.children_11_16:
            parts.append(f"{self.children_11_16} дітей 11-16р")
        return f"{self.tour.title} – {', '.join(parts)}: {self.price} грн"


class PriceCalendar(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='price_calendar', verbose_name="Тур")
    date = models.DateField(verbose_name="Дата")
    duration = models.PositiveSmallIntegerField(
        verbose_name="Тривалість (ночей)",
        help_text="Кількість ночей"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ціна (грн)",
        null=True,
        blank=True,
        help_text="Вкажіть ціну в гривнях (наприклад: 15000.00). Залиште порожнім, якщо немає пропозиції"
    )

    class Meta:
        verbose_name = "Календар цін"
        verbose_name_plural = "Календарі цін"
        ordering = ['date', 'duration']
        unique_together = ('tour', 'date', 'duration')

    def __str__(self):
        return f"{self.tour.title} – {self.date} ({self.duration} ночей) – {self.price if self.price else 'н/д'}"


class AmenityCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок сортування")

    class Meta:
        verbose_name = "Категорія послуг"
        verbose_name_plural = "Категорії послуг"
        ordering = ['order']

    def __str__(self):
        return self.name


class AmenityName(models.Model):
    category = models.ForeignKey(AmenityCategory, on_delete=models.CASCADE, related_name='possible_names', verbose_name="Категорія")
    name = models.CharField(max_length=200, verbose_name="Назва послуги")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок сортування")
    is_popular_default = models.BooleanField(default=False, verbose_name="Популярна за замовчуванням")

    class Meta:
        verbose_name = "Можлива назва послуги"
        verbose_name_plural = "Можливі назви послуг"
        ordering = ['category__order', 'order']
        unique_together = ('category', 'name')

    def __str__(self):
        return self.name


class Amenity(models.Model):
    category = models.ForeignKey(AmenityCategory, on_delete=models.CASCADE, related_name='amenities', verbose_name="Категорія")
    name = ChainedForeignKey(
        AmenityName,
        chained_field="category",
        chained_model_field="category",
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name="Назва послуги"
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок сортування")
    is_popular = models.BooleanField(default=False, verbose_name="Популярна (для виділення)")

    class Meta:
        verbose_name = "Послуга"
        verbose_name_plural = "Послуги"
        ordering = ['category__order', 'order']
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.name} ({self.category.name})"