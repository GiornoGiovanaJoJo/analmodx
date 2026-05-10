/*
 * Lightweight homepage carousel for m-trud.ru.
 *
 * Safe load order when js/function.js has not yet been patched:
 *   js/owl.carousel.js
 *   js/mt-mobile-carousel.js
 *   js/function.js
 *
 * If js/function.js is patched to skip [data-mt-carousel], this file can also
 * be loaded after js/function.js. The script guards the existing Owl initializer
 * from touching marked sliders and enhances those sliders with native
 * scroll-snap pagination. No Owl wrappers are created for the marked homepage
 * sliders.
 */
(function (window, document) {
  'use strict';

  var CAROUSEL_SELECTOR = '[data-mt-carousel]';
  var DOTS_CLASS = 'mt-carousel-dots';
  var DOT_CLASS = 'mt-carousel-dot';
  var ACTIVE_CLASS = 'is-active';
  var states = [];

  function forEachNode(nodes, callback) {
    Array.prototype.forEach.call(nodes, callback);
  }

  function directSlides(slider) {
    return Array.prototype.filter.call(slider.children, function (child) {
      return !child.classList.contains(DOTS_CLASS);
    });
  }

  function clampIndex(index, length) {
    if (index < 0) {
      return 0;
    }
    if (index >= length) {
      return length - 1;
    }
    return index;
  }

  function currentIndex(slider, length) {
    if (!length || !slider.clientWidth) {
      return 0;
    }
    return clampIndex(Math.round(slider.scrollLeft / slider.clientWidth), length);
  }

  function setActiveDot(state, index) {
    state.index = clampIndex(index, state.dots.length);
    state.dots.forEach(function (dot, dotIndex) {
      var isActive = dotIndex === state.index;
      dot.classList.toggle(ACTIVE_CLASS, isActive);
      dot.setAttribute('aria-selected', isActive ? 'true' : 'false');
      dot.setAttribute('tabindex', isActive ? '0' : '-1');
    });
  }

  function scrollToSlide(state, index) {
    var slideIndex = clampIndex(index, state.slides.length);
    var left = slideIndex * state.slider.clientWidth;

    state.slider.scrollTo({
      left: left,
      behavior: 'smooth'
    });

    setActiveDot(state, slideIndex);
  }

  function buildDots(slider, slides) {
    var dots = document.createElement('div');
    dots.className = DOTS_CLASS;
    dots.setAttribute('role', 'tablist');
    dots.setAttribute('aria-label', 'Навигация по слайдеру');

    slides.forEach(function (_slide, index) {
      var dot = document.createElement('button');
      dot.className = DOT_CLASS;
      dot.type = 'button';
      dot.setAttribute('role', 'tab');
      dot.setAttribute('aria-label', 'Показать слайд ' + (index + 1));
      dot.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
      dot.setAttribute('tabindex', index === 0 ? '0' : '-1');
      dots.appendChild(dot);
    });

    slider.insertAdjacentElement('afterend', dots);
    return dots;
  }

  function initSlider(slider) {
    if (slider.getAttribute('data-mt-carousel-ready') === '1') {
      return;
    }

    var slides = directSlides(slider);
    if (slides.length < 2) {
      slider.setAttribute('data-mt-carousel-ready', '1');
      return;
    }

    var dotsWrapper = buildDots(slider, slides);
    var state = {
      slider: slider,
      slides: slides,
      dots: Array.prototype.slice.call(dotsWrapper.querySelectorAll('.' + DOT_CLASS)),
      index: 0,
      scrollTimer: null
    };

    state.dots.forEach(function (dot, index) {
      dot.addEventListener('click', function () {
        scrollToSlide(state, index);
      });
    });

    slider.addEventListener('scroll', function () {
      if (state.scrollTimer) {
        window.clearTimeout(state.scrollTimer);
      }
      state.scrollTimer = window.setTimeout(function () {
        setActiveDot(state, currentIndex(slider, slides.length));
      }, 80);
    }, { passive: true });

    states.push(state);
    slider.setAttribute('data-mt-carousel-ready', '1');
    setActiveDot(state, 0);
  }

  function initMarkedSliders() {
    forEachNode(document.querySelectorAll(CAROUSEL_SELECTOR), initSlider);
  }

  function loadCarouselStyles() {
    if (document.querySelector('link[href*="mt-mobile-carousel.css"]')) {
      return;
    }

    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/mt-mobile-carousel.css?v=20260510c';
    document.head.appendChild(link);
  }

  function scheduleCarouselStyles() {
    window.setTimeout(loadCarouselStyles, 1000);
  }

  function refreshActiveDots() {
    states.forEach(function (state) {
      setActiveDot(state, currentIndex(state.slider, state.slides.length));
    });
  }

  function installOwlGuard() {
    var $ = window.jQuery;
    if (!$ || !$.fn || !$.fn.owlCarousel || $.fn.owlCarousel.__mtCarouselGuard) {
      return;
    }

    var originalOwlCarousel = $.fn.owlCarousel;

    function guardedOwlCarousel() {
      var marked = this.filter(CAROUSEL_SELECTOR);
      var legacy = this.not(CAROUSEL_SELECTOR);

      marked.each(function () {
        initSlider(this);
      });

      if (legacy.length) {
        originalOwlCarousel.apply(legacy, arguments);
      }

      return this;
    }

    for (var property in originalOwlCarousel) {
      if (Object.prototype.hasOwnProperty.call(originalOwlCarousel, property)) {
        guardedOwlCarousel[property] = originalOwlCarousel[property];
      }
    }

    guardedOwlCarousel.__mtCarouselGuard = true;
    guardedOwlCarousel.__mtOriginal = originalOwlCarousel;
    $.fn.owlCarousel = guardedOwlCarousel;
  }

  installOwlGuard();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMarkedSliders);
  } else {
    initMarkedSliders();
  }

  if (document.readyState === 'complete') {
    scheduleCarouselStyles();
  } else {
    window.addEventListener('load', scheduleCarouselStyles, { once: true });
  }

  window.addEventListener('resize', refreshActiveDots, { passive: true });
  window.addEventListener('orientationchange', refreshActiveDots, { passive: true });
}(window, document));
