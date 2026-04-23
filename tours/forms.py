from django import forms
from .models import Consultation, Review

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['name', 'phone', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше ім\'я'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваш телефон'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ваш коментар (необов\'язково)'}),
        }
        labels = {
            'name': 'Ім\'я',
            'phone': 'Телефон',
            'comment': 'Коментар',
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поділіться враженнями про тур...'
            }),
        }
        labels = {
            'rating': 'Ваша оцінка',
            'comment': 'Ваш відгук',
        }


# ДОДАЙТЕ ЦЮ ФОРМУ
class GuestReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['guest_name', 'rating', 'comment']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ваше ім'я"}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ваш відгук'}),
        }
        labels = {
            'guest_name': "Ваше ім'я",
            'rating': "Оцінка",
            'comment': "Коментар",
        }

class PriceSearchForm(forms.Form):
    """Форма для пошуку цін на тур з розширеним вибором міста вильоту"""
    departure_city = forms.ChoiceField(
        label="Звідки",
        choices=[
            ('', '---------'),
            ('Без транспорту', 'Без транспорту'),
            # Австрія
            ('з Відня (літак)', 'Австрія: з Відня (літак)'),
            # Бельгія
            ('з Брюсселя (літак)', 'Бельгія: з Брюсселя (літак)'),
            # Естонія
            ('з Таллінна (літак)', 'Естонія: з Таллінна (літак)'),
            # Іспанія
            ('з Мадрида (літак)', 'Іспанія: з Мадрида (літак)'),
            # Італія
            ('з Турина (літак)', 'Італія: з Турина (літак)'),
            ('з Рима (літак)', 'Італія: з Рима (літак)'),
            ('з Мілана (літак)', 'Італія: з Мілана (літак)'),
            ('з Болоньї (літак)', 'Італія: з Болоньї (літак)'),
            # Латвія
            ('з Риги (літак)', 'Латвія: з Риги (літак)'),
            # Литва
            ('з Вільнюса (літак)', 'Литва: з Вільнюса (літак)'),
            # Молдова
            ('з Кишинева (літак)', 'Молдова: з Кишинева (літак)'),
            # Нідерланди
            ('з Амстердама (літак)', 'Нідерланди: з Амстердама (літак)'),
            # Німеччина
            ('з Дортмунда (літак)', 'Німеччина: з Дортмунда (літак)'),
            ('з Падерборна (літак)', 'Німеччина: з Падерборна (літак)'),
            ('з Касселя (літак)', 'Німеччина: з Касселя (літак)'),
            ('з Фрідріхсхафена (літак)', 'Німеччина: з Фрідріхсхафена (літак)'),
            ('з Нюрнберга (літак)', 'Німеччина: з Нюрнберга (літак)'),
            ('з Мюнхена (літак)', 'Німеччина: з Мюнхена (літак)'),
            ('з Франкфурта-на-Майні (літак)', 'Німеччина: з Франкфурта-на-Майні (літак)'),
            ('з Дюссельдорфа (літак)', 'Німеччина: з Дюссельдорфа (літак)'),
            ('з Дрездена (літак)', 'Німеччина: з Дрездена (літак)'),
            ('з Кельна (літак)', 'Німеччина: з Кельна (літак)'),
            ('з Берліна (літак)', 'Німеччина: з Берліна (літак)'),
            # Польща
            ('з Ольштина (літак)', 'Польща: з Ольштина (літак)'),
            ('з Лодзя (літак)', 'Польща: з Лодзя (літак)'),
            ('з Бидгоща (літак)', 'Польща: з Бидгоща (літак)'),
            ('з Зеленої Гури (літак)', 'Польща: з Зеленої Гури (літак)'),
            ('з Жешува (літак)', 'Польща: з Жешува (літак)'),
            ('з Катовіце (літак)', 'Польща: з Катовіце (літак)'),
            ('з Любліна (літак)', 'Польща: з Любліна (літак)'),
            ('з Вроцлава (літак)', 'Польща: з Вроцлава (літак)'),
            ('з Познаня (літак)', 'Польща: з Познаня (літак)'),
            ('з Кракова (літак)', 'Польща: з Кракова (літак)'),
            ('з Гданська (літак)', 'Польща: з Гданська (літак)'),
            ('з Варшави (літак)', 'Польща: з Варшави (літак)'),
            # Румунія
            ('з Бакеу (літак)', 'Румунія: з Бакеу (літак)'),
            ('з Брашова (літак)', 'Румунія: з Брашова (літак)'),
            ('з Крайови (літак)', 'Румунія: з Крайови (літак)'),
            ('з Ораді (літак)', 'Румунія: з Ораді (літак)'),
            ('з Сібіу (літак)', 'Румунія: з Сібіу (літак)'),
            ('з Яссів (літак)', 'Румунія: з Яссів (літак)'),
            ('з Клуж-Напоки (літак)', 'Румунія: з Клуж-Напоки (літак)'),
            ('з Бая-Маре (літак)', 'Румунія: з Бая-Маре (літак)'),
            ('з Тімішоари (літак)', 'Румунія: з Тімішоари (літак)'),
            ('з Сучави (літак)', 'Румунія: з Сучави (літак)'),
            ('з Бухареста (літак)', 'Румунія: з Бухареста (літак)'),
            # Словаччина
            ('з Братислави (літак)', 'Словаччина: з Братислави (літак)'),
            # Угорщина
            ('з Будапешта (літак)', 'Угорщина: з Будапешта (літак)'),
            # Україна
            ('з Києва (автобус)', 'Україна: з Києва (автобус)'),
            # Чехія
            ('з Острави (літак)', 'Чехія: з Острави (літак)'),
            ('з Праги (літак)', 'Чехія: з Праги (літак)'),
        ],
        initial='з Кишинева (літак)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        label="Початок туру",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    duration_min = forms.IntegerField(
        label="Тривалість від",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'від'})
    )
    duration_max = forms.IntegerField(
        label="до",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'до'})
    )
    adults = forms.IntegerField(
        label="Дорослих",
        min_value=1,
        initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        duration_min = cleaned_data.get('duration_min')
        duration_max = cleaned_data.get('duration_max')
        if duration_min and duration_max and duration_min > duration_max:
            raise forms.ValidationError("Мінімальна тривалість не може бути більшою за максимальну.")
        return cleaned_data