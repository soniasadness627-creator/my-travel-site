from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone', 'is_agent')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Применяем Bootstrap класс ко всем полям
        for field_name, field in self.fields.items():
            if field_name != 'is_agent':
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Простая валидация телефона (можно расширить)
        if phone and not phone.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise forms.ValidationError("Введіть коректний номер телефону")
        return phone