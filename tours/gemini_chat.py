import random
import requests
import json
from django.db import models
from django.urls import reverse
from django.utils.http import urlencode
from .models import Tour

GEMINI_API_KEY = "AIzaSyAlyvwC7SmSESF7YpCOUJRuYgTLIP7b7L4"


def get_min_price_for_country(country_name):
    try:
        tours = Tour.objects.filter(country__icontains=country_name)
        if tours.exists():
            min_price = tours.aggregate(models.Min('price'))['price__min']
            if min_price:
                return int(min_price)
        return None
    except Exception as e:
        print(f"Помилка отримання ціни для {country_name}: {e}")
        return None


def get_countries_with_prices(request=None):
    try:
        countries_data = {}
        tours = Tour.objects.all()

        # Фільтруємо тури для агента, якщо є агентський сайт
        if request:
            from tours.views import filter_tours_by_agent_site
            tours = filter_tours_by_agent_site(tours, request)

        for tour in tours:
            country = tour.country
            if country not in countries_data or tour.price < countries_data[country]:
                countries_data[country] = tour.price
        return countries_data
    except Exception as e:
        print(f"Помилка отримання країн: {e}")
        return {}


def get_gemini_response(message, request, agency_name="Моя Агенція"):
    """
    Отримує відповідь від Gemini API з урахуванням агентського контексту
    """
    last_country = request.session.get('chat_last_country', None)
    message_lower = message.lower()
    agent_site = getattr(request, 'current_agent_site', None)

    # Список країн для перевірки
    countries_list = ['Єгипет', 'Туреччина', 'ОАЕ', 'Таїланд', 'Мальдіви', 'Іспанія', 'Італія', 'Кіпр', 'Греція',
                      'Чехія']

    # Обробка "так" - перенаправлення на пошук
    yes_words = ['так', 'да', 'yes', '+', 'ok', 'звісно', 'так, цікавить']
    if any(w in message_lower for w in yes_words) and last_country:
        if agent_site:
            redirect_url = f'/a/{agent_site.slug}/search/?country={last_country}&chat_open=1&chat_country={last_country}'
        else:
            redirect_url = f'/search/?country={last_country}&chat_open=1&chat_country={last_country}'
        request.session.pop('chat_last_country', None)
        return {'text': f"🔍 Переходжу до турів в {last_country}. Зачекайте...", 'redirect': redirect_url}

    # Обробка "ні"
    no_words = ['ні', 'нет', 'no', 'не', 'не треба']
    if any(w in message_lower for w in no_words) and last_country:
        request.session.pop('chat_last_country', None)
        return {'text': "Добре! Тоді розкажіть, що саме вас цікавить? Наприклад, інша країна або бюджет.",
                'redirect': None}

    # Розпізнавання країни
    countries_prices = get_countries_with_prices(request)
    found_country = None

    country_variants = {
        'Єгипет': ['єгипет', 'єгипту', 'єгипті', 'єгиптом', 'єгипте', 'египет'],
        'Туреччина': ['туреччина', 'туреччину', 'туреччині', 'туреччиною', 'турция'],
        'ОАЕ': ['оае', 'оає', 'дубай', 'дубаї', 'дубаєм'],
        'Таїланд': ['таїланд', 'таїланду', 'таїланді', 'тайланд'],
        'Мальдіви': ['мальдіви', 'мальдів', 'мальдівах', 'мальдивы'],
        'Іспанія': ['іспанія', 'іспанію', 'іспанії', 'испания'],
        'Італія': ['італія', 'італію', 'італії', 'италия'],
        'Кіпр': ['кіпр', 'кипр'],
        'Греція': ['греція', 'грецію', 'греції', 'греция'],
        'Чехія': ['чехія', 'чехію', 'чехії', 'чехия'],
    }

    # Спочатку шукаємо пряме співпадіння
    for country in countries_prices.keys():
        if country.lower() in message_lower:
            found_country = country
            break

    # Якщо не знайшли, шукаємо за варіантами
    if not found_country:
        for canonical, variants in country_variants.items():
            for variant in variants:
                if variant in message_lower:
                    for country in countries_prices.keys():
                        if country.lower() == canonical.lower():
                            found_country = country
                            break
                    if found_country:
                        break
            if found_country:
                break

    # Якщо знайшли країну
    if found_country:
        price = countries_prices[found_country]
        request.session['chat_last_country'] = found_country
        return {
            'text': f"🇪🇬 {found_country} - чудовий вибір! Мінімальна ціна туру в {found_country} складає {int(price)} $ за 7 ночей. Хочете дізнатися більше про готелі або конкретні дати? (Так/Ні)",
            'redirect': None
        }

    # Вітання
    greeting_words = ["привіт", "вітаю", "добрий день", "доброго", "hi", "hello", "здравствуйте"]
    if any(w in message_lower for w in greeting_words):
        names = ["Анна", "Олександр", "Марія", "Дмитро", "Олена", "Іван", "Тетяна", "Михайло", "Наталія", "Сергій"]
        bot_name = random.choice(names)
        return {
            'text': f"👋 Вітаю! Радий вас бачити в {agency_name}. Мене звати {bot_name}. Чим можу допомогти з підбором туру?",
            'redirect': None
        }

    # Ціни
    price_words = ["ціни", "вартість", "скільки коштує", "прайс", "ціна", "бюджет", "сколько стоит"]
    if any(w in message_lower for w in price_words):
        if countries_prices:
            response_text = "💰 Актуальні мінімальні ціни на тури:\n"
            for country, price in sorted(countries_prices.items(), key=lambda x: x[1])[:10]:
                response_text += f"• {country}: від {int(price)} $\n"
            response_text += "\nХочете дізнатися деталі по конкретній країні? Напишіть назву країни."
            return {'text': response_text, 'redirect': None}
        else:
            return {
                'text': "💰 На жаль, зараз немає актуальних турів. Але ви можете залишити заявку, і наш менеджер підбере варіанти: <a href=\"#consultationCard\">👇 Заповнити форму</a>",
                'redirect': None
            }

    # Напрямки
    directions_words = ["куди", "поїхати", "напрямок", "популярні", "рекомендуєте"]
    if any(w in message_lower for w in directions_words):
        if countries_prices:
            top_countries = sorted(countries_prices.items(), key=lambda x: x[1])[:5]
            response_text = "🌍 Популярні напрямки з актуальними цінами:\n"
            for country, price in top_countries:
                response_text += f"• {country}: від {int(price)} $\n"
            response_text += "\nЯка країна вас цікавить?"
            return {'text': response_text, 'redirect': None}
        else:
            return {'text': "🌍 Популярні напрямки: Єгипет, Туреччина, ОАЕ, Таїланд, Мальдіви. Який вас цікавить?",
                    'redirect': None}

    # Прощання
    bye_words = ["пока", "бувай", "до побачення", "до свидания"]
    if any(w in message_lower for w in bye_words):
        return {'text': "👋 До побачення! Буду радий допомогти вам з підбором туру. Заходьте ще!", 'redirect': None}

    # Якщо нічого не підійшло – пропонуємо консультацію з HTML-посиланням
    return {
        'text': "🤖 Вибачте, я не зміг знайти відповідь на ваше запитання. Але ви можете залишити заявку, і наш менеджер зв'яжеться з вами для детальної консультації: <a href=\"#consultationCard\">👇 Залишити заявку</a>",
        'redirect': None
    }