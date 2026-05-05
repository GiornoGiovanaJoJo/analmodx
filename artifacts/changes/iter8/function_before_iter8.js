$(document).ready(function(){
    $('a[href="#simple-order"]').click(function(){
        var minorder = $(this).data('minorder');
        if(minorder == '' || minorder < 1){
          minorder = 1;
        }
        // $('#simple-order input[name="count"]').val(minorder);
        $('#simple-order .mincount').text(minorder);
    });
    $('body').on('click','.checkFormSubmit',function(){
        var form = $(this).closest('form');
        if(form.find('input[name="formName"]').val() == form.find('input[name="checkForm"]').val()){
            form.find('input[name="checkForm"]').val('allRight');
        }
    });
    $('.btn-menu').on('click',function(){
        $('.side-menu').toggleClass('active');
        $('.fade-bg').toggleClass('active');
    })
        $('.fade-bg').on('click',function(){
        $(this).toggleClass('active');
        $('.side-menu').toggleClass('active');
    })
        $('#fadeMe').readMoreFade();
        $('#camera_wrap').camera({
            loader: true,
            pagination: true,
            minHeight: '249',
            thumbnails: false,
            height: '32.51538461%',
            caption: true,
            navigation: true,
            fx:  'scrollBottom'
        });
        
        function initPopupMethods() {
            // Удаляем предыдущие обработчики, чтобы избежать дублирования
            $(".make-order, #various1").off('click.fb-start click.openform');

            // Для экранов больше 768px - Fancybox
            if (window.innerWidth > 768) {
                $(".make-order").fancybox();
                $("#various1").fancybox();
                $(".various").fancybox();
            } 
            // Для экранов 768px и меньше - OpenForm
            else {
                $(".make-order").openform();
                $("#various1").openform();
                $(".various").openform();
            }
        }
        // Создаем функцию openform
        $.fn.openform = function() {
            this.on('click', function(e) {
                e.preventDefault();
                
                // 1. Показываем блок formsblock на весь экран
                $('#formsblock').css('display', 'block');
                
                // 2. Получаем ID формы из атрибута href
                var hrefValue = $(this).attr('href');
                var formId = (hrefValue === '#text') ? '#consult-form' : hrefValue;
                
                // 3. Скрываем все формы и показываем только нужную
                $('#formsblock > div[id]').hide(); // Скрываем все формы (div с id)
                $(formId).show(); // Показываем нужную форму
                
                // 4. Обработчик для кнопки закрытия
                $('.formsblockclose').off('click').on('click', function() {
                    $('#formsblock').hide();
                    $('#formsblock > div[id]').show(); // Показываем все формы снова
                });
            });
        };
        // Инициализируем при загрузке
        initPopupMethods();

        // Обновляем при изменении размера окна
        $(window).on('resize', function() {
            initPopupMethods();
        });
        $('a#various1').click(function(){
           if($(this).data('change') == 1)
           {
               $('#text span').text($(this).data('title'));
               $('#text .card_but_submit').val($(this).data('btn'));
           }
        });
        $("#contact_phone").mask("+9(999) 999-9999");

        // Функция для запрета цифр
        function preventNumbers(e) {
            // Разрешаем: backspace, delete, tab, escape, enter
            if ($.inArray(e.keyCode, [46, 8, 9, 27, 13]) !== -1 ||
               // Разрешаем: Ctrl+A, Ctrl+C, Ctrl+X
               (e.keyCode == 65 && e.ctrlKey === true) || 
               (e.keyCode == 67 && e.ctrlKey === true) ||
               (e.keyCode == 88 && e.ctrlKey === true) ||
               // Разрешаем: стрелки, home, end
               (e.keyCode >= 35 && e.keyCode <= 39)) {
                 return;
            }
            
            // Запрещаем цифры (0-9 и numpad)
            if ((e.keyCode >= 48 && e.keyCode <= 57) || (e.keyCode >= 96 && e.keyCode <= 105)) {
              e.preventDefault();
            }
        }

        // Применяем к нужным полям
        $('input[name="catalog_name"], input[name="card_name"], input[name="contact_name"]').on("keydown", preventNumbers);

        $("#owl, #owl-ready-interest").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: true,
            navigation : true
        });
        $("#owl-ready-interest").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: false,
            navigation : true
        });
        $("#owl-ready").owlCarousel({
            items : 5,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: false,
            navigation : true
        });
        $("#owl-ready-same").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: true,
            navigation : true
        });  
        $("#owl-ready-same2").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: false,
            navigation : true
        });  
        $("#owl-ready-same3").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: false,
            navigation : true
        });     
        $("#owl-ready-same4").owlCarousel({
            items : 4,
            itemsDesktop : [995,3],
            itemsDesktopSmall : [767, 1],
            itemsTablet: [700, 1],
            itemsMobile : [479, 1],
            lazyLoad : true,
            pagination: false,
            navigation : true
        });          
        /*Back to Top*/
        $().UItoTop({ easingType: 'easeOutQuart' });
        // $("a.various").fancybox();

        $("a[rel=group]").fancybox({
            'transitionIn' : 'none',
            'transitionOut' : 'none',
            'titlePosition' : 'over',
            'showNavArrows' : 'true',
            'centerOnScroll' : 'true',
            'cyclic' : 'false',
            'enableEscapeButton' : 'true',
            'titleFormat' : function(title, currentArray, currentIndex, currentOpts) {
            return '<span id="fancybox-title-over">Image ' + (currentIndex + 1) + ' / ' + currentArray.length + (title.length ? ' &nbsp; ' + title : '') + '</span>';
            }
        });
        $("a[rel=group1]").fancybox({
            'transitionIn' : 'none',
            'transitionOut' : 'none',
            'titlePosition' : 'over',
            'showNavArrows' : 'true',
            'centerOnScroll' : 'true',
            'cyclic' : 'false',
            'enableEscapeButton' : 'true',
            'titleFormat' : function(title, currentArray, currentIndex, currentOpts) {
            return '<span id="fancybox-title-over">Image ' + (currentIndex + 1) + ' / ' + currentArray.length + (title.length ? ' &nbsp; ' + title : '') + '</span>';
            }
        });

        $(".make-order").on("click", function(e) {
              if ($(this).attr("data-source") !== "") {
                $("[name='card_source']").val($(this).attr("data-source"));
              }
              if ($(this).attr("data-url") !== "") {
                $("[name='page_url']").val($(this).attr("data-url"));
              }     
            if ($(this).attr("data-minorder") !== "") {
                $("[name='count']").attr("min",$(this).attr("data-minorder"));
              }  
        });

    $("table .make-order").on("click", function(e) {
      var source = 'таблица ' + $(this).closest("table").siblings("h2").text() + ' ',
        index  = $(this).closest("tr").children().index($(this).closest("td"));
        
      source += $(this).closest("tbody").find("tr:first-child > td:nth-child(" + ++index + ")").text();
      $("[name='card_source']").val(source);

    });
    $('a[href*="#"]:not([href="#text"]):not(.various):not([href="#simple-order"])').click(function(e) {
      e.preventDefault();
      var target = $(this.hash);
      console.log(target);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      
      if (target.length) {
        $('html, body').animate({
        scrollTop: target.offset().top
        }, 1500);
        return false;
      }
    });
    $('a[data-popup]').on('click', function() {
      var win = window.open('tech/popup/popup1', "popup", "location=1,status=1,scrollbars=1, resizable=1, directories=1, toolbar=1, titlebar=1, width=640, height=480, top=160. left=240");
            console.log(1);
      $.ajax({
        method: 'POST',
        url: 'tech/popup/',
        data: {
          popup: $(this).attr('data-popup')
        },
        success: function(result) {
          win.document.write(result);
          console.log(2);
        }
      });
    });
    $(".announce_gallery").lightGallery();
    $('.side-menu-gallery').owlCarousel({
          autoPlay: true,
            navigation: true,
            slideSpeed: 300,
            paginationSpeed: 400,
            singleItem:true
      });
  });
  function owlInitialize() {
   if ($(window).width() < 500) {
      $('.mobile-slider').owlCarousel(
      {
        items: 1,
        autoHeight : true,
        lazyLoad : true,
        navigation: true,
      }
    );
   }else{
       $('.mobile-slider').trigger('destroy.owl.carousel');
   }
}

$(document).ready(function(e) {
   owlInitialize();
});

$(window).resize(function() {
   owlInitialize();
});
    $(document).on("click", ".submenu-slave .open ", function (e) {
        e.stopPropagation();
        var el = $(this);
        if (el.closest(".submenu-slave").hasClass('active')) {

            $(this).closest(".submenu-slave").find(".submenu-slave-block").slideUp(1200, function () {
                el.closest(".submenu-slave").removeClass('active');
            });

        } else {

            $(this).closest(".submenu-slave").find(".submenu-slave-block").slideDown(1200, function () {
                el.closest(".submenu-slave").addClass('active');
            });
        }
    });
    $(document).on("click", ".submenu-main .open-main", function (e) {
        var el = $(this);
        if (el.closest(".submenu-main").hasClass('active')) {

            $(this).closest(".submenu-main").find(".submenu-main-block").slideUp(1200, function () {
                el.closest(".submenu-main").removeClass('active');
            });

        } else {

            $(this).closest(".submenu-main").find(".submenu-main-block").slideDown(1200, function () {
                el.closest(".submenu-main").addClass('active');
            });
        }
    });
      if (document.documentElement.clientWidth <= 500) {
        $('.submenu-main').addClass('active');
         $('.submenu-slave').addClass('active');
    }




// $(function () {

//   const $carousel = $(".review-carousel");
//   const $allCards = $(".review-card");

//   function resetOwlHeights() {
//     $(".owl-item").css("height", "auto");
//     $(".owl-stage").css("height", "auto");
//   }

//   function createCarousel(cards) {
//     if ($carousel.data('owlCarousel')) {
//     $carousel.data('owlCarousel').destroy();

//     // Полная очистка того, что сделал Owl v1
//     $carousel.removeClass('owl-carousel owl-loaded');
//     $carousel.find('.owl-wrapper, .owl-item').children().unwrap();

//     $carousel.html(""); 
// }

//     $carousel.html(cards.clone(true));

//     // $carousel.owlCarousel({
//     //   items: 3,
//     //   margin: 20,
//     //   nav: true,
//     //   dots: true,
//     //   navText: ["‹", "›"],
//     //   responsive: { 
//     //     0: { items: 1 },
//     //     768: { items: 3 }
//     //   },
//     //   onInitialized: resetOwlHeights,
//     //   onResized: resetOwlHeights
//     // });

//     $carousel.owlCarousel({
//         items: 3, 
//         itemsDesktop: [1199, 3],
//         itemsDesktopSmall: [979, 3],
//         itemsTablet: [768, 1], 
//         itemsMobile: [479, 1],

//         navigation: true,
//         navigationText: ["", ""],

//         pagination: true,
//         paginationNumbers: false,

//         autoHeight: false,
//         afterInit: function() {
//       resetOwlHeights();
//       setTimeout(function(){
//         initReadMore($carousel); 
//       }, 30);
//     },
//     afterUpdate: function() {
//       resetOwlHeights();
//       setTimeout(function(){
//         initReadMore($carousel);
//       }, 30);
//     }
//     });


//     setTimeout(resetOwlHeights, 30);
//     setTimeout(() => initReadMore($carousel), 50);
//   }


//   if ($(".filter-buttons button").length) {
//     $(".filter-buttons button").on("click", function () {
//       $(".filter-buttons button").removeClass("active");
//       $(this).addClass("active");

//       const cat = $(this).data("category");
//       createCarousel($allCards.filter(`[data-category="${cat}"]`));
//     });

//     const defCat = $(".filter-buttons button.active").data("category");
//     createCarousel($allCards.filter(`[data-category="${defCat}"]`));
//   } else {
//     createCarousel($allCards);
//   }

//   let t;
//   $(window).on("resize", function () {
//     clearTimeout(t);
//     t = setTimeout(() => {
//       if ($(".filter-buttons button").length) {
//         const cat = $(".filter-buttons button.active").data("category");
//         createCarousel($allCards.filter(`[data-category="${cat}"]`));
//       } else {
//         createCarousel($allCards);
//       }
//     }, 200);
//   });
// });


// function initReadMore($container) {
//   $container.find(".review-text").each(function () {
//     const $text = $(this);

//     if ($text.next(".read-more").length) return;

//     const full = getNaturalHeight($text[0]);
//     const limited = $text[0].clientHeight;

//     if (full - limited > 10) {
//       $('<div class="read-more">Читать далее</div>').insertAfter($text);
//     }
//   });
// }

// function getNaturalHeight(el) {
//   const clone = el.cloneNode(true);
//   clone.style.position = "absolute";
//   clone.style.visibility = "hidden";
//   clone.style.height = "auto";
//   clone.style.display = "block";
//   clone.style.webkitLineClamp = "unset";
//   el.parentNode.appendChild(clone);
//   const h = clone.scrollHeight;
//   clone.remove();
//   return h;
// }

// $(document).on("click", ".read-more", function () {
//   const $btn = $(this);
//   const $text = $btn.prev(".review-text");

//   if ($text.hasClass("expanded")) {
//     $text.removeClass("expanded").css({
//       "-webkit-line-clamp": "3",
//       overflow: "hidden"
//     });
//     $btn.text("Читать далее");
//   } else {
//     $text.addClass("expanded").css({
//       "-webkit-line-clamp": "unset",
//       overflow: "visible"
//     });
//     $btn.text("Свернуть");
//   }

//   $(".owl-stage").css("height", "auto");
// });
$(function () {

  // ---------------------------
  // ИНИЦИАЛИЗАЦИЯ БЛОКА
  // ---------------------------
  function initReviewsBlock($block) {
    const $carousel = $block.find(".review-carousel");
    const $allCards = $block.find(".review-card");
    const $filterButtons = $block.find(".filter-buttons button");

    // ---------------------------
    // УНИЧТОЖЕНИЕ КАРУСЕЛИ
    // ---------------------------
    function destroyCarousel() {
      const owl = $carousel.data("owlCarousel");
      if (owl) {
        owl.destroy();
        $carousel
          .removeClass("owl-carousel owl-loaded")
          .find(".owl-wrapper, .owl-item")
          .children()
          .unwrap();
        $carousel.empty();
      }
    }

    // ---------------------------
    // СОЗДАНИЕ КАРУСЕЛИ
    // ---------------------------
    function createCarousel(cards) {
      destroyCarousel();
      $carousel.html(cards.clone(true));

      $carousel.owlCarousel({
        items: 3,
        itemsDesktop: [1199, 3],
        itemsDesktopSmall: [979, 3],
        itemsTablet: [768, 1],
        itemsMobile: [479, 1],
        navigation: true,
        navigationText: ["", ""],
        pagination: true,
        autoHeight: false,
        afterInit: fixHeights,
        afterUpdate: fixHeights
      });

      setTimeout(() => {
        fixHeights();
        initReadMore($carousel);
      }, 50);
    }

    // ---------------------------
    // ВСПОМОГАТЕЛЬНЫЕ
    // ---------------------------
    function fixHeights() {
      $block.find(".owl-item, .owl-stage").css("height", "auto");
    }

    function filterCards(cat) {
      return $allCards.filter(function () {
        const categories = $(this).data("category").toString().split(/\s+/);
        return categories.includes(cat);
      });
    }

    // ---------------------------
    // ФИЛЬТР
    // ---------------------------
    if ($filterButtons.length) {
      $filterButtons.on("click", function () {
        $filterButtons.removeClass("active");
        $(this).addClass("active");

        const cat = $(this).data("category");
        createCarousel(filterCards(cat));
      });
    }

    // ---------------------------
    // ПЕРВИЧНЫЙ ЗАПУСК ПО window.load
    // (решает проблему мобильной версии)
    // ---------------------------
    $(window).on("load", function () {
      let cards;

      if ($filterButtons.length) {
        const defCat = $filterButtons.filter(".active").data("category");
        cards = filterCards(defCat);
      } else {
        cards = $allCards;
      }

      createCarousel(cards);
    });

    // ---------------------------
    // RESIZE (по необходимости)
    // ---------------------------
    let t;
    $(window).on("resize", function () {
      clearTimeout(t);
      t = setTimeout(() => {
        if ($filterButtons.length) {
          const cat = $filterButtons.filter(".active").data("category");
          createCarousel(filterCards(cat));
        } else {
          createCarousel($allCards);
        }
      }, 200);
    });
  }

  // ---------------------------
  // Запуск для всех блоков
  // ---------------------------
  $(".reviews").each(function () {
    initReviewsBlock($(this));
  });
});


// ---------------------------
// READ MORE
// ---------------------------
function initReadMore($container) {
  $container.find(".review-text").each(function () {
    const $text = $(this);

    if ($text.next(".read-more").length) return;

    const full = getNaturalHeight($text[0]);
    const limited = $text[0].clientHeight;

    if (full - limited > 10) {
      $('<div class="read-more">Читать далее</div>').insertAfter($text);
    }
  });
}

function getNaturalHeight(el) {
  const clone = el.cloneNode(true);
  clone.style.position = "absolute";
  clone.style.visibility = "hidden";
  clone.style.height = "auto";
  clone.style.display = "block";
  clone.style.webkitLineClamp = "unset";
  el.parentNode.appendChild(clone);
  const h = clone.scrollHeight;
  clone.remove();
  return h;
}

$(document).on("click", ".read-more", function () {
  const $btn = $(this);
  const $text = $btn.prev(".review-text");
  const $imageWrapper = $btn.closest(".review-card").find(".review-image-wrapper");


  if ($text.hasClass("expanded")) {
    $text.removeClass("expanded").css({
      "-webkit-line-clamp": "3",
      overflow: "hidden"
    });
    $btn.text("Читать далее");
    $imageWrapper.addClass("hidden");
  } else {
    $text.addClass("expanded").css({
      "-webkit-line-clamp": "unset",
      overflow: "visible"
    });
    $btn.text("Свернуть");
    $imageWrapper.removeClass("hidden");
  }

  $(".owl-stage").css("height", "auto");
});

const items = document.querySelectorAll('.accordion-item');
items.forEach(item => {
  item.querySelector('.accordion-header').addEventListener('click', () => {
    const content = item.querySelector('.accordion-content');
    const isOpen = item.classList.contains('active');

    items.forEach(i => {
      i.classList.remove('active');
      i.querySelector('.accordion-content').style.maxHeight = null;
      i.querySelector('.accordion-content').classList.remove('open');
    });

    if (!isOpen) {
      item.classList.add('active');
      content.style.maxHeight = content.scrollHeight + 'px';
      content.classList.add('open');
    }
  });
});


// document.addEventListener('DOMContentLoaded', function () {
//     const fileInput = document.querySelector('input[name="attachment"]');
//     const form = document.querySelector('#catalog_form');
//     const maxSize = 10 * 1024 * 1024; // 10 МБ

//     const allowedExtensions = ['jpg', 'jpeg', 'ai', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'xlsm', 'cdr', 'webp', 'png'];

//     function validateFile(fileInput) {
//         if (fileInput.files.length === 0) return true;

//         const file = fileInput.files[0];
//         const fileSize = file.size;
//         const fileName = file.name.toLowerCase();
//         const extension = fileName.split('.').pop();

//         // Проверка размера
//         if (fileSize > maxSize) {
//             alert('Файл не должен превышать 10 МБ');
//             fileInput.value = '';
//             return false;
//         }

//         // Проверка расширения
//         if (!allowedExtensions.includes(extension)) {
//             alert('Допустимые форматы: JPG, PNG, WEBP, PDF, DOC, DOCX');
//             fileInput.value = '';
//             return false;
//         }

//         return true;
//     }

//     fileInput.addEventListener('change', function () {
//         validateFile(this);
//     });

//     form.addEventListener('submit', function (e) {
//         if (!validateFile(fileInput)) {
//             e.preventDefault();
//         }
//     });
// });

document.addEventListener('DOMContentLoaded', function () {
    const maxSize = 10 * 1024 * 1024; // 10 МБ
    const allowedExtensions = ['jpg', 'jpeg', 'ai', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'xlsm', 'cdr', 'webp', 'png'];

    function validateFile(fileInput) {
        if (fileInput.files.length === 0) return true;

        const file = fileInput.files[0];
        const fileSize = file.size;
        const fileName = file.name.toLowerCase();
        const extension = fileName.split('.').pop();

        // Проверка размера
        if (fileSize > maxSize) {
            alert('Файл не должен превышать 10 МБ');
            fileInput.value = '';
            return false;
        }

        // Проверка расширения
        if (!allowedExtensions.includes(extension)) {
            alert('Допустимые форматы: JPG, PNG, WEBP, PDF, DOC, DOCX');
            fileInput.value = '';
            return false;
        }

        return true;
    }

    function setupFormValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const fileInput = form.querySelector('input[name="attachment"]');
        if (!fileInput) return;

        fileInput.addEventListener('change', function () {
            validateFile(this);
        });

        form.addEventListener('submit', function (e) {
            if (!validateFile(fileInput)) {
                e.preventDefault();
            }
        });
    }

    // Настраиваем валидацию для обеих форм по их ID
    setupFormValidation('catalog_form');
    setupFormValidation('card_form');
});


$(document).ready(function() {
    $('a[href="#text"]').on('click', function(e) {
        e.preventDefault(); // предотвращаем стандартный переход по ссылке

        // через 600 мс изменяем текст
        //setTimeout(function() {
            $('.catalog_form').each(function () {
                var $form = $(this);
                var minValue = $form.find('input[name="count"]').attr('min');
                
                if (minValue) {
                    $form.find('.mincount').text(minValue);
                }
            });
        //}, 400);
    });
});