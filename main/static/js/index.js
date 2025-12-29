// Intersection Observer for authors animations
document.addEventListener('DOMContentLoaded', function() {
    const authorItems = document.querySelectorAll('.content-item');

    const observerOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    authorItems.forEach(item => {
        observer.observe(item);
    });
});

// Old animation system for .hidden elements
const elements = document.querySelectorAll('.hidden');

function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function showElements() {
    elements.forEach((el) => {
        if (isElementInViewport(el)) {
            el.classList.add('show');
        }
    });
}

window.addEventListener('scroll', showElements);
window.addEventListener('load', showElements);

    document.addEventListener("DOMContentLoaded", function() {
      const text = "Bine ați venit la Penița Dreptului"; 
      let index = 0;
      const titleElement = document.querySelector('.typing'); 
  
      function type() {
          if (index < text.length) {
              titleElement.textContent += text.charAt(index); 
              index++;
              setTimeout(type, 60);
          }
      }
  
      type();
  });
  
  document.addEventListener("DOMContentLoaded", function () {
      const slider = document.querySelector(".news-slider");
      let isDown = false;
      let startX;
      let scrollLeft;
    
      slider.addEventListener("mousedown", (e) => {
        isDown = true;
        slider.classList.add("active");
        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
      });
    
      slider.addEventListener("mouseleave", () => {
        isDown = false;
        slider.classList.remove("active");
      });
    
      slider.addEventListener("mouseup", () => {
        isDown = false;
        slider.classList.remove("active");
      });
    
      slider.addEventListener("mousemove", (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 3; // Скорость прокрутки
        slider.scrollLeft = scrollLeft - walk;
      });
    });
  