document.addEventListener('DOMContentLoaded', function() {
  // Seleccionar los elementos del DOM
    const carousel = document.querySelector('.carousel-product4-2');
    const slides = document.querySelectorAll('.product-card4-2');
    const prevBtn = document.querySelector('.btn-left-prd2');
    const nextBtn = document.querySelector('.btn-right-prd2');
    const dotsContainer = document.querySelector('.carousel-dots2');

  // Variables de control
    let currentIndex = 0;
    let slideWidth = 0;
    let slidesToShow = 1;
    let totalGroups = 1;
    let gapSize = 30; // Gap por defecto entre tarjetas (30px en desktop)

  // Calcula el ancho de las tarjetas y el espacio entre ellas según el viewport
    function calculateDimensions() {
    // Obtener el ancho actual de una tarjeta
    const cardWidth = slides[0].offsetWidth;
    
    // Determinar el tamaño del gap según el ancho de la ventana
    if (window.innerWidth <= 430) {
      gapSize = 20; // Gap de 20px en móviles pequeños
    } else if (window.innerWidth <= 580) {
      gapSize = 20; // Gap de 20px en móviles medianos
    } else {
      gapSize = 30; // Gap de 30px en desktop
    }
    
    // Actualizar el ancho de slide (tarjeta + gap)
    slideWidth = cardWidth + gapSize;
    
    return { cardWidth, gapSize };
    }
    
  // Calcula cuántos slides se pueden mostrar a la vez según el ancho de la ventana
    function calculateSlidesPerView() {
    const { cardWidth, gapSize } = calculateDimensions();
    const containerWidth = carousel.parentElement.clientWidth;
    
    // Ajustar para considerar el padding del contenedor
    // El padding es 50px en desktop y 20px en móviles
    let containerPadding = window.innerWidth <= 430 ? 40 : 100;
    
    // Calcular cuántas tarjetas caben en el contenedor considerando gap y padding
    slidesToShow = Math.max(1, Math.floor((containerWidth - containerPadding) / slideWidth));
    
    // Asegurar que no se intente mostrar más tarjetas de las que existen
    slidesToShow = Math.min(slidesToShow, slides.length);
    
    // Calcular el número total de grupos
    totalGroups = Math.ceil(slides.length / slidesToShow);
    
    // Asegurar que el índice actual sea válido después de recalcular
    if (currentIndex > slides.length - slidesToShow) {
        currentIndex = Math.max(0, slides.length - slidesToShow);
    }
    
    // Regenerar los puntos indicadores y actualizar la UI
    generateDots();
    updateCarousel();
    }
    
  // Genera los puntos indicadores basados en el número de grupos de slides
    function generateDots() {
    dotsContainer.innerHTML = '';
    for (let i = 0; i < totalGroups; i++) {
        const dot = document.createElement('div');
        dot.classList.add('carousel-dot2');
        if (i === Math.floor(currentIndex / slidesToShow)) {
        dot.classList.add('active');
        }
        dot.addEventListener('click', () => {
        goToGroup(i);
        });
        dotsContainer.appendChild(dot);
    }
    }
    
  // Navega a un grupo específico de slides
    function goToGroup(groupIndex) {
    currentIndex = groupIndex * slidesToShow;
    // Asegurar que no excedamos el límite de slides
    if (currentIndex > slides.length - slidesToShow) {
        currentIndex = slides.length - slidesToShow;
    }
    updateCarousel();
    } 
    
  // Inicialización al cargar la página
    calculateSlidesPerView();
    
  // Eventos para los botones de navegación
    prevBtn.addEventListener('click', () => {
    currentIndex = Math.max(currentIndex - slidesToShow, 0);
    updateCarousel();
    });
    
    nextBtn.addEventListener('click', () => {
    currentIndex = Math.min(currentIndex + slidesToShow, slides.length - slidesToShow);
    updateCarousel();
    });
    
  // Actualiza la posición y estilos del carrusel
    function updateCarousel() {
    // Recalcular dimensiones antes de desplazar
    calculateDimensions();
    
    // Actualizar la posición de desplazamiento con animación suave
    carousel.scrollTo({
      left: currentIndex * slideWidth,
        behavior: 'smooth'
    });
    
    // Actualizar el punto indicador activo
    const activeDotIndex = Math.floor(currentIndex / slidesToShow);
    const dots = document.querySelectorAll('.carousel-dot2');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === activeDotIndex);
    });
    
    // Actualizar el estado de los botones (opacidad)
    prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
    prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
    
    const lastIndex = slides.length - slidesToShow;
    nextBtn.style.opacity = currentIndex >= lastIndex ? '0.5' : '1';
    nextBtn.style.pointerEvents = currentIndex >= lastIndex ? 'none' : 'auto';
    }
    
  // Manejar el redimensionamiento de la ventana
    let resizeTimeout;
    window.addEventListener('resize', () => {
    // Limitar la frecuencia de ejecución del evento resize
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        calculateSlidesPerView();
    }, 250);
    });

  // Funcionalidad de deslizamiento táctil
    let touchStartX = 0;
    let touchEndX = 0;
    
    carousel.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    carousel.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
    }, { passive: true });
    
  // Manejar el gesto de deslizamiento
    function handleSwipe() {
    // Ajustar el umbral de deslizamiento según el tamaño de la pantalla
    const swipeThreshold = window.innerWidth <= 430 ? 30 : 50;
    
    if (touchStartX - touchEndX > swipeThreshold) {
      // Deslizar a la izquierda - ir al siguiente
        if (currentIndex < slides.length - slidesToShow) {
        currentIndex += slidesToShow;
        updateCarousel();
        }
    } else if (touchEndX - touchStartX > swipeThreshold) {
      // Deslizar a la derecha - ir al anterior
        if (currentIndex > 0) {
        currentIndex -= slidesToShow;
        updateCarousel();
        }
    }
    }
    
  // Prevenir comportamiento por defecto al arrastrar
    carousel.addEventListener('dragstart', (e) => {
    e.preventDefault();
    });
});