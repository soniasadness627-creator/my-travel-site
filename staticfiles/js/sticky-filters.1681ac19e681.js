// Фіксація фільтрів при прокрутці
document.addEventListener('DOMContentLoaded', function() {
    // Знаходимо контейнер фільтрів за різними класами
    const filters = document.querySelector('.sidebar-filters, .filter-sidebar, .filters-column, .filters, .col-lg-3, #filterForm');

    if (filters) {
        function checkSticky() {
            const windowHeight = window.innerHeight;
            const filtersHeight = filters.offsetHeight;

            // Якщо висота вікна більша за висоту фільтрів + 100px
            if (windowHeight > filtersHeight + 100) {
                filters.style.position = 'sticky';
                filters.style.top = '20px';
                filters.style.alignSelf = 'flex-start';
                filters.style.height = 'fit-content';
            } else {
                // Для маленьких екранів прибираємо sticky
                if (window.innerWidth <= 768) {
                    filters.style.position = 'relative';
                    filters.style.top = 'auto';
                }
            }
        }

        // Викликаємо при завантаженні
        checkSticky();

        // Викликаємо при зміні розміру вікна
        window.addEventListener('resize', checkSticky);

        // Викликаємо при прокрутці (для додаткової надійності)
        window.addEventListener('scroll', checkSticky);
    }
});