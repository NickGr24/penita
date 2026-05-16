// Mark page as JS-loaded so animations only apply when JS works
document.documentElement.classList.add('js-loaded');

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
      const titleElement = document.querySelector('.typing');
      const text = titleElement.textContent.trim();
      let index = 0;
      titleElement.textContent = '';

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

  document.addEventListener("DOMContentLoaded", function () {
      const items = document.querySelectorAll(".faq-item");
      if (!items.length) return;

      items.forEach(item => {
          const summary = item.querySelector("summary");
          if (!summary) return;

          const panel = document.createElement("div");
          panel.className = "faq-panel";
          Array.from(item.children).forEach(child => {
              if (child !== summary) panel.appendChild(child);
          });
          item.appendChild(panel);

          if (!item.open) panel.style.height = "0px";

          let animating = false;

          summary.addEventListener("click", (e) => {
              e.preventDefault();
              if (animating) return;
              animating = true;

              if (item.open) {
                  panel.style.height = panel.scrollHeight + "px";
                  requestAnimationFrame(() => {
                      panel.style.height = "0px";
                  });
                  panel.addEventListener("transitionend", function handler(ev) {
                      if (ev.propertyName !== "height") return;
                      panel.removeEventListener("transitionend", handler);
                      item.open = false;
                      animating = false;
                  });
              } else {
                  item.open = true;
                  panel.style.height = "0px";
                  requestAnimationFrame(() => {
                      panel.style.height = panel.scrollHeight + "px";
                  });
                  panel.addEventListener("transitionend", function handler(ev) {
                      if (ev.propertyName !== "height") return;
                      panel.removeEventListener("transitionend", handler);
                      panel.style.height = "auto";
                      animating = false;
                  });
              }
          });
      });
  });
