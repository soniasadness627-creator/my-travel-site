// Динамічне завантаження міст залежно від обраної країни (чистий JS)
document.addEventListener('DOMContentLoaded', function() {
    // Знаходимо поле країни та міста
    const countryField = document.getElementById('id_country');
    const cityField = document.getElementById('id_city');

    if (!countryField || !cityField) {
        console.log('Поля не знайдені');
        return;
    }

    // Функція для завантаження міст
    function loadCities() {
        const country = countryField.value;

        if (!country) {
            // Очищаємо список міст
            cityField.innerHTML = '';
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '---------';
            cityField.appendChild(defaultOption);
            return;
        }

        // Показуємо індикатор завантаження
        cityField.innerHTML = '';
        const loadingOption = document.createElement('option');
        loadingOption.value = '';
        loadingOption.textContent = 'Завантаження...';
        loadingOption.disabled = true;
        cityField.appendChild(loadingOption);
        cityField.disabled = true;

        // AJAX запит
        fetch(`/a/admin/get-cities/?country=${encodeURIComponent(country)}`)
            .then(response => response.json())
            .then(data => {
                cityField.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '---------';
                cityField.appendChild(defaultOption);

                if (data.length > 0) {
                    data.forEach(function(city) {
                        const option = document.createElement('option');
                        option.value = city.id;
                        option.textContent = city.name;
                        cityField.appendChild(option);
                    });
                } else {
                    const noOption = document.createElement('option');
                    noOption.value = '';
                    noOption.textContent = 'Немає міст для цієї країни';
                    noOption.disabled = true;
                    cityField.appendChild(noOption);
                }
                cityField.disabled = false;
            })
            .catch(error => {
                console.error('Помилка завантаження міст:', error);
                cityField.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '---------';
                cityField.appendChild(defaultOption);

                const errorOption = document.createElement('option');
                errorOption.value = '';
                errorOption.textContent = 'Помилка завантаження';
                errorOption.disabled = true;
                cityField.appendChild(errorOption);
                cityField.disabled = false;
            });
    }

    // Завантажуємо міста при зміні країни
    countryField.addEventListener('change', loadCities);

    // Завантажуємо міста при завантаженні сторінки (якщо країна вже вибрана)
    if (countryField.value) {
        loadCities();
    }
});