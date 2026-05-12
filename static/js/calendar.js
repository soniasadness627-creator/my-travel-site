// ========== КАЛЕНДАР НИЗЬКИХ ЦІН ==========
document.addEventListener('DOMContentLoaded', function() {
    // Оновлений список країн для кожного міста вильоту
    const countryListByDepartureCity = {
        "Кишинів": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Чорногорія", "Хорватія", "Греція", "Туніс", "Таїланд", "Грузія", "Італія", "Португалія"],
        "Варшава": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Чорногорія", "Греція", "Туніс", "Таїланд", "Грузія", "Португалія"],
        "Краків": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Хорватія", "Греція", "Туніс", "Грузія"],
        "Бухарест": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Чорногорія", "Греція", "Туніс", "Грузія"],
        "Будапешт": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Хорватія", "Греція", "Туніс", "Грузія"],
        "Берлін": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Чорногорія", "Греція", "Туніс", "Грузія"],
        "Прага": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Хорватія", "Греція", "Туніс", "Грузія"],
        "Тбілісі": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Греція", "Туніс", "Грузія"],
        "Стамбул": ["Єгипет", "Туреччина", "ОАЕ", "Шрі Ланка", "Іспанія", "Мальдіви", "Кіпр", "Греція", "Туніс", "Грузія"]
    };

    let currentCountry = '';
    let currentMonth = new Date();
    currentMonth.setMonth(4);
    let currentDeparture = 'Кишинів';

    const calendarDays = document.getElementById('calendarDays');
    const monthYearDisplay = document.getElementById('monthYearDisplay');
    const prevBtn = document.getElementById('prevMonthBtn');
    const nextBtn = document.getElementById('nextMonthBtn');
    const departureSelect = document.getElementById('departureCitySelect');
    const maxPriceSpan = document.querySelector('.price-range-indicator .max-price');
    const minPriceSpan = document.querySelector('.price-range-indicator .min-price');
    const countryTabsContainer = document.querySelector('.country-tabs');

    function rebuildCountryTabs(departureCity) {
        const countries = countryListByDepartureCity[departureCity];
        if (!countries) return;

        countryTabsContainer.innerHTML = '';
        countries.forEach((country, idx) => {
            const btn = document.createElement('button');
            btn.className = 'country-tab' + (idx === 0 ? ' active' : '');
            btn.setAttribute('data-country', country);
            btn.textContent = country;
            btn.addEventListener('click', function() {
                document.querySelectorAll('.country-tab').forEach(tab => tab.classList.remove('active'));
                this.classList.add('active');
                currentCountry = this.getAttribute('data-country');
                updateCalendar();
            });
            countryTabsContainer.appendChild(btn);
        });
        currentCountry = countries[0];
        updateCalendar();
    }

    // ========== API ДЛЯ ОТРИМАННЯ ЦІН ==========
    async function fetchPriceData(country, month, departure) {
        const year = month.getFullYear();
        const monthIndex = month.getMonth() + 1;
        let url = `/api/calendar-prices/?country=${encodeURIComponent(country)}&year=${year}&month=${monthIndex}&departure=${encodeURIComponent(departure)}`;

        // Додаємо slug для агентських сайтів
        const slugFromUrl = window.location.pathname.split('/')[2];
        if (slugFromUrl && slugFromUrl !== '') {
            url += `&slug=${slugFromUrl}`;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log('✅ Отримано ціни для календаря:', data.prices?.length, 'днів');
            return { prices: data.prices, maxPrice: data.max_price };
        } catch (error) {
            console.error('❌ Помилка завантаження цін:', error);
            const daysInMonth = new Date(year, monthIndex, 0).getDate();
            return { prices: new Array(daysInMonth).fill(null), maxPrice: null };
        }
    }

    function getColorForPrice(price, minPrice, maxPrice) {
        if (price === null) return 'gray';
        if (price === minPrice) return 'low';
        if (price === maxPrice) return 'red';
        if (maxPrice - minPrice === 0) return 'medium';
        const ratio = (price - minPrice) / (maxPrice - minPrice);
        if (ratio < 0.33) return 'low';
        if (ratio < 0.66) return 'medium';
        return 'red';
    }

    function getHeightForPrice(price, minPrice, maxPrice) {
        if (price === null) return 30;
        if (minPrice === maxPrice) return 50;
        const ratio = (price - minPrice) / (maxPrice - minPrice);
        return 20 + (ratio * 80);
    }

    function renderCalendar(prices) {
        if (!calendarDays) return;

        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        calendarDays.innerHTML = '';

        const validPrices = prices.filter(p => p !== null);
        let globalMin = null;
        let globalMax = null;

        if (validPrices.length > 0) {
            globalMin = Math.min(...validPrices);
            globalMax = Math.max(...validPrices);
        }

        if (globalMin !== null) {
            minPriceSpan.innerHTML = `від ${globalMin.toLocaleString('uk-UA')} ₴`;
            minPriceSpan.style.color = '#28a745';
        } else {
            minPriceSpan.innerHTML = 'немає даних';
        }

        if (globalMax !== null) {
            maxPriceSpan.innerHTML = `до ${globalMax.toLocaleString('uk-UA')} ₴`;
            maxPriceSpan.style.color = '#dc3545';
        } else {
            maxPriceSpan.innerHTML = 'немає даних';
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        for (let day = 1; day <= daysInMonth; day++) {
            const price = prices[day - 1];
            const dayDate = new Date(year, month, day);
            const dayOfWeek = dayDate.toLocaleDateString('uk', { weekday: 'short' });
            const dateISO = `${year}-${String(month+1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

            const col = document.createElement('div');
            col.className = 'day-column';

            if (dayDate < today) {
                col.innerHTML = `<div class="day-week">${dayOfWeek}</div><div class="day-date">${day}</div><div class="price-bar-container"><div class="price-column gray" style="height: 20%;"></div></div><div class="price-value-text" style="color: #adb5bd;">пройшло</div>`;
            } else if (price !== null) {
                const barClass = getColorForPrice(price, globalMin, globalMax);
                const barHeight = getHeightForPrice(price, globalMin, globalMax);
                col.setAttribute('onclick', `selectCalendarDate('${dateISO}', ${price}, 7)`);
                col.style.cursor = 'pointer';
                col.innerHTML = `<div class="day-week">${dayOfWeek}</div><div class="day-date">${day}</div><div class="price-bar-container"><div class="price-column ${barClass}" style="height: ${barHeight}%;"></div></div><div class="price-value-text" style="color: ${barClass === 'low' ? '#28a745' : (barClass === 'red' ? '#dc3545' : '#ffc107')}">${Math.round(price).toLocaleString('uk-UA')} ₴</div>`;
            } else {
                col.innerHTML = `<div class="day-week">${dayOfWeek}</div><div class="day-date">${day}</div><div class="price-bar-container"><div class="price-column gray" style="height: 20%;"></div></div><div class="price-value-text" style="color: #adb5bd;">немає</div>`;
            }
            calendarDays.appendChild(col);
        }
    }

    async function updateCalendar() {
        if (!currentCountry || !currentDeparture) return;
        monthYearDisplay.textContent = currentMonth.toLocaleString('uk', { month: 'long', year: 'numeric' });
        if (calendarDays) calendarDays.innerHTML = '<div class="text-center w-100 py-5">Завантаження...</div>';
        const { prices } = await fetchPriceData(currentCountry, currentMonth, currentDeparture);
        renderCalendar(prices);
    }

    function onDepartureChange() {
        currentDeparture = departureSelect.value;
        rebuildCountryTabs(currentDeparture);
    }

    if (departureSelect) {
        currentDeparture = departureSelect.value;
        departureSelect.addEventListener('change', onDepartureChange);
        rebuildCountryTabs(currentDeparture);
    }

    if (prevBtn) prevBtn.addEventListener('click', () => { currentMonth.setMonth(currentMonth.getMonth() - 1); updateCalendar(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { currentMonth.setMonth(currentMonth.getMonth() + 1); updateCalendar(); });
});