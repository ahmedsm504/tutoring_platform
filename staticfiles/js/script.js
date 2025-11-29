// Toggle Mobile Menu
function toggleMenu() {
    const navLinks = document.getElementById('navLinks');
    navLinks.classList.toggle('active');
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const nav = document.querySelector('.main-nav');
    const navLinks = document.getElementById('navLinks');
    const toggle = document.querySelector('.menu-toggle');
    
    if (!nav.contains(event.target) && window.innerWidth <= 968) {
        navLinks.classList.remove('active');
    }
});

// Close menu when clicking a link on mobile
if (window.innerWidth <= 968) {
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            document.getElementById('navLinks').classList.remove('active');
        });
    });
}

// Notification System for Supervisors
(function () {
    const meta = document.querySelector('meta[name="is-supervisor"]');
    const isSupervisor = meta && meta.content === '1';
    if (!isSupervisor) return;

    function updateNotificationCount() {
        fetch('/api/unread-count/')
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById('notificationBadge');
                const count = data.total_unread || 0;
                
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.classList.add('active');
                    
                    if (!window.location.pathname.includes('supervisor/dashboard')) {
                        document.title = `(${count}) رسائل جديدة - مؤسسة العجمي`;
                    }
                } else {
                    badge.classList.remove('active');
                    if (!window.location.pathname.includes('supervisor/dashboard')) {
                        document.title = 'مؤسسة العجمي';
                    }
                }
            })
            .catch(error => console.error('Error:', error));
    }

    updateNotificationCount();
    setInterval(updateNotificationCount, 30000);
})();

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});