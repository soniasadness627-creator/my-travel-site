// Динамічне завантаження міст залежно від обраної країни
document.addEventListener('DOMContentLoaded', function() {
    const countryField = document.querySelector('#id_country');
    const cityField = document.querySelector('#id_city');

    if (!countryField || !cityField) {
        console.log('Поля не знайдені');
        return;
    }

    console.log('JS завантажено, початкова країна:', countryField.value);

    function updateCities() {
        const country = countryField.value;
        const currentCityValue = cityField.value;

        console.log('Оновлення міст для країни:', country);

        // Очищаємо поле city
        cityField.innerHTML = '<option value="">---------</option>';
        cityField.disabled = true;

        if (!country) {
            cityField.disabled = false;
            return;
        }

        // Відправляємо AJAX запит
        // Використовуємо шлях /a/admin/get-cities/
        fetch(`/a/admin/get-cities/?country=${encodeURIComponent(country)}`)
            .then(response => {
                console.log('Відповідь отримано, статус:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP помилка: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Отримані міста:', data);
                cityField.disabled = false;

                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(function(city) {
                        const option = document.createElement('option');
                        option.value = city.id;
                        option.textContent = city.name;
                        cityField.appendChild(option);
                    });

                    // Якщо було попереднє значення - відновлюємо
                    if (currentCityValue && currentCityValue !== '') {
                        cityField.value = currentCityValue;
                    }
                } else {
                    console.log('Міст не знайдено для країни:', country);
                }
            })
            .catch(error => {
                console.error('Помилка завантаження міст:', error);
                cityField.disabled = false;
                cityField.innerHTML = '<option value="">---------</option><option value="" disabled>Помилка завантаження</option>';
            });
    }

    // Слухаємо зміну країни
    countryField.addEventListener('change', updateCities);

    // Якщо країна вже вибрана - завантажуємо міста
    if (countryField.value) {
        updateCities();
    }
});