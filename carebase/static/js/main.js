document.addEventListener('DOMContentLoaded', () => {
    const navbar = document.querySelector('.navbar');
    
    // 1. Scroll Effect: Shrink navbar on scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.height = '60px';
            navbar.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
        } else {
            navbar.style.height = '80px';
            navbar.style.boxShadow = 'none';
        }
    });

    // 2. Active Link Highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = '#3182CE'; // Accent blue
            link.style.fontWeight = '700';
        }
    });

    // 3. Simple Form Validation for Contact Page
    const contactForm = document.querySelector('form');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            const emailInput = document.querySelector('input[type="email"]');
            if (emailInput && !emailInput.value.includes('@')) {
                e.preventDefault();
                alert('Please enter a valid clinic communication email.');
            }
        });
    }
});