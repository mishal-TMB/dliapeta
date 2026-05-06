// Scroll reveal
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.08 });

document.querySelectorAll('.feat-card, .card, .mod-card, .news-card, .gallery-ph, .donat-card, .donat-step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(18px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    observer.observe(el);
});

// Active nav on scroll
const sections = document.querySelectorAll('section[id], header[id]');
const links = document.querySelectorAll('.nav-links a');
window.addEventListener('scroll', () => {
    let cur = '';
    sections.forEach(s => {
        if (window.scrollY >= s.offsetTop - 100) cur = s.id;
    });
    links.forEach(a => {
        const href = a.getAttribute('href');
        if (href && href.startsWith('#')) {
            a.classList.toggle('active', href === `#${cur}`);
        }
    });
}, { passive: true });
