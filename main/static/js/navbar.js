document.addEventListener("DOMContentLoaded", function() {
    const menuIcon = document.getElementById('menu-icon');
    const navLinks = document.getElementById('nav-links');

    menuIcon.addEventListener('click', () => {
        navLinks.classList.toggle('nav-active');
        menuIcon.classList.toggle('toggle');
        // Sync body class so CSS can hide higher-z-index elements
        // (PDF fullscreen-btn, etc.) while the mobile menu is open.
        document.body.classList.toggle('menu-open',
            navLinks.classList.contains('nav-active'));
    });
});
