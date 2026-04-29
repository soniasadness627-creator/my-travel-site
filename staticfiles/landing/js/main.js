// ========== ЛЕНДИНГ - JavaScript ==========

document.addEventListener('DOMContentLoaded', function() {
    // Закріплена навігація (зміна прозорості при скролі)
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('shadow-md');
                navbar.classList.add('bg-white/95');
                navbar.classList.add('backdrop-blur-md');
            } else {
                navbar.classList.remove('shadow-md');
                navbar.classList.remove('bg-white/95');
                navbar.classList.remove('backdrop-blur-md');
            }
        });
    }

    // Мобільне меню
    const menuBtn = document.getElementById('menuBtn');
    const closeMenuBtn = document.getElementById('closeMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');

    if (menuBtn && closeMenuBtn && mobileMenu) {
        menuBtn.addEventListener('click', function() {
            mobileMenu.classList.remove('translate-x-full');
            mobileMenu.classList.add('translate-x-0');
        });

        closeMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.remove('translate-x-0');
            mobileMenu.classList.add('translate-x-full');
        });

        // Закриття меню при кліку на посилання
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', function() {
                mobileMenu.classList.remove('translate-x-0');
                mobileMenu.classList.add('translate-x-full');
            });
        });
    }

    // Плавний скрол для всіх якірних посилань
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                const navbarHeight = 80;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - navbarHeight;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Обробка форми
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ВІДПРАВЛЯЄМО...';
            submitBtn.disabled = true;

            // Тут можна додати відправку на сервер
            setTimeout(() => {
                submitBtn.innerHTML = '✓ ВІДПРАВЛЕНО!';
                submitBtn.style.backgroundColor = '#22c55e';

                setTimeout(() => {
                    contactForm.reset();
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    submitBtn.style.backgroundColor = '';
                }, 2000);
            }, 1500);
        });
    }
});