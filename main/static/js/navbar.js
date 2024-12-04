document.addEventListener("DOMContentLoaded", function() {
    const menuIcon = document.getElementById('menu-icon');
    const navLinks = document.getElementById('nav-links');
    
    menuIcon.addEventListener('click', () => {
        navLinks.classList.toggle('nav-active');
        menuIcon.classList.toggle('toggle');
    });
});
