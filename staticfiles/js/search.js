document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const resultsBox = document.getElementById("searchResults");
    const searchForm = searchInput ? searchInput.closest('form') : null;

    if (!searchInput) return;

    let searchTimeout;

    // Изменяем action формы для поиска
    if (searchForm) {
        searchForm.action = "/search/";
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimeout);

        let query = this.value.trim();

        if (query.length < 2) {
            resultsBox.innerHTML = "";
            resultsBox.style.display = "none";
            return;
        }

        // Показываем индикатор загрузки
        resultsBox.innerHTML = "<div class='list-group-item'>Пошук...</div>";
        resultsBox.style.display = "block";

        searchTimeout = setTimeout(() => {
            fetch(`/live-search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsBox.innerHTML = "";

                    if (data.length === 0) {
                        resultsBox.innerHTML = "<div class='list-group-item'>Нічого не знайдено</div>";
                        resultsBox.style.display = "block";
                        return;
                    }

                    data.forEach(tour => {
                        const div = document.createElement("a");
                        div.href = `/tour/${tour.id}/`;
                        div.className = "list-group-item";
                        div.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${tour.title}</strong>
                                    <br>
                                    <small><i class="fa-solid fa-location-dot"></i> ${tour.country}</small>
                                </div>
                                <span class="price-tag">${tour.price} $</span>
                            </div>
                        `;
                        resultsBox.appendChild(div);
                    });

                    resultsBox.style.display = "block";
                })
                .catch(error => {
                    console.error(error);
                    resultsBox.innerHTML = "<div class='list-group-item text-danger'>Помилка пошуку</div>";
                    resultsBox.style.display = "block";
                });
        }, 300);
    });

    // Обработчик Enter - отправляем форму на страницу поиска
    searchInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            if (searchForm) {
                searchForm.submit();
            }
        }
    });

    // Закрывать при клике вне
    document.addEventListener("click", function (e) {
        if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
            resultsBox.style.display = "none";
        }
    });
});