// Carousel Configuration
const carouselConfig = {
    features: {
        track: null,
        currentIndex: 0,
        totalCards: 0,
        visibleCards: 4,
        autoScrollInterval: null,
        isHovered: false,
        autoScrollDelay: 3000
    },
    support: {
        track: null,
        currentIndex: 0,
        totalCards: 0,
        visibleCards: 4,
        autoScrollInterval: null,
        isHovered: false,
        autoScrollDelay: 3000
    }
};

// Initialize Carousels
function initCarousels() {
    initCarousel('features');
    initCarousel('support');
}

// Initialize Individual Carousel
function initCarousel(type) {
    const config = carouselConfig[type];
    config.track = document.getElementById(`${type}-carousel`);
    
    if (!config.track) return;
    
    const cards = config.track.children;
    config.totalCards = cards.length;
    
    // Clone cards for infinite loop effect
    const clonedCards = Array.from(cards).map(card => card.cloneNode(true));
    clonedCards.forEach(card => config.track.appendChild(card));
    
    // Update visible cards based on screen size
    updateVisibleCards(type);
    
    // Create indicators
    createIndicators(type);
    
    // Add hover listeners
    addHoverListeners(type);
    
    // Start auto-scroll
    startAutoScroll(type);
    
    // Add resize listener
    window.addEventListener('resize', () => {
        updateVisibleCards(type);
        updateCarouselPosition(type);
    });
}

// Update Visible Cards Based on Screen Size
function updateVisibleCards(type) {
    const config = carouselConfig[type];
    const width = window.innerWidth;
    
    if (width <= 600) {
        config.visibleCards = 1;
    } else if (width <= 900) {
        config.visibleCards = 2;
    } else if (width <= 1200) {
        config.visibleCards = 3;
    } else {
        config.visibleCards = 4;
    }
}

// Move Carousel
function moveCarousel(type, direction) {
    const config = carouselConfig[type];
    
    // Stop auto-scroll temporarily
    stopAutoScroll(type);
    
    config.currentIndex += direction;
    
    // Handle boundaries
    if (config.currentIndex < 0) {
        config.currentIndex = config.totalCards - 1;
    } else if (config.currentIndex >= config.totalCards) {
        config.currentIndex = 0;
    }
    
    updateCarouselPosition(type);
    updateIndicators(type);
    
    // Restart auto-scroll after 5 seconds
    setTimeout(() => {
        if (!config.isHovered) {
            startAutoScroll(type);
        }
    }, 5000);
}

// Update Carousel Position
function updateCarouselPosition(type) {
    const config = carouselConfig[type];
    const cardWidth = config.track.children[0].offsetWidth;
    const gap = 20;
    const offset = config.currentIndex * (cardWidth + gap);
    
    config.track.style.transform = `translateX(${offset}px)`;
    
    // Handle infinite loop
    if (config.currentIndex >= config.totalCards) {
        setTimeout(() => {
            config.track.style.transition = 'none';
            config.currentIndex = 0;
            config.track.style.transform = `translateX(0px)`;
            setTimeout(() => {
                config.track.style.transition = 'transform 0.5s ease-in-out';
            }, 50);
        }, 500);
    }
}

// Create Indicators
function createIndicators(type) {
    const config = carouselConfig[type];
    const indicatorsContainer = document.getElementById(`${type}-indicators`);
    
    if (!indicatorsContainer) return;
    
    indicatorsContainer.innerHTML = '';
    
    for (let i = 0; i < config.totalCards; i++) {
        const indicator = document.createElement('div');
        indicator.className = 'carousel-indicator';
        if (i === 0) indicator.classList.add('active');
        
        indicator.addEventListener('click', () => {
            stopAutoScroll(type);
            config.currentIndex = i;
            updateCarouselPosition(type);
            updateIndicators(type);
            
            setTimeout(() => {
                if (!config.isHovered) {
                    startAutoScroll(type);
                }
            }, 5000);
        });
        
        indicatorsContainer.appendChild(indicator);
    }
}

// Update Indicators
function updateIndicators(type) {
    const config = carouselConfig[type];
    const indicators = document.querySelectorAll(`#${type}-indicators .carousel-indicator`);
    
    indicators.forEach((indicator, index) => {
        if (index === config.currentIndex) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    });
}

// Auto-scroll Functionality
function startAutoScroll(type) {
    const config = carouselConfig[type];
    
    stopAutoScroll(type);
    
    config.autoScrollInterval = setInterval(() => {
        if (!config.isHovered) {
            moveCarousel(type, -1); // Move left (RTL direction)
        }
    }, config.autoScrollDelay);
}

function stopAutoScroll(type) {
    const config = carouselConfig[type];
    
    if (config.autoScrollInterval) {
        clearInterval(config.autoScrollInterval);
        config.autoScrollInterval = null;
    }
}

// Add Hover Listeners
function addHoverListeners(type) {
    const config = carouselConfig[type];
    const section = config.track.closest('.carousel-section');
    
    if (!section) return;
    
    section.addEventListener('mouseenter', () => {
        config.isHovered = true;
        stopAutoScroll(type);
    });
    
    section.addEventListener('mouseleave', () => {
        config.isHovered = false;
        startAutoScroll(type);
    });
}

// Intersection Observer for Auto-start
function setupIntersectionObserver() {
    const options = {
        root: null,
        threshold: 0.3
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const type = entry.target.querySelector('.carousel-track').id.replace('-carousel', '');
            const config = carouselConfig[type];
            
            if (entry.isIntersecting && !config.isHovered) {
                startAutoScroll(type);
            } else {
                stopAutoScroll(type);
            }
        });
    }, options);
    
    document.querySelectorAll('.carousel-section').forEach(section => {
        observer.observe(section);
    });
}

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', () => {
    initCarousels();
    setupIntersectionObserver();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopAutoScroll('features');
    stopAutoScroll('support');
});

// Hero Video Loading Function with Error Handling
function loadHeroVideo() {
    const wrapper = document.getElementById('hero-video-wrapper');
    const placeholder = document.getElementById('hero-video-placeholder');
    
    if (!wrapper || !placeholder) return;
    
    // Your YouTube video ID
    const videoId = 'YOUR_VIDEO_ID_HERE'; // Replace with actual ID
    
    // Create iframe
    const iframe = document.createElement('iframe');
      iframe.src = 'https://www.youtube.com/embed/d7-WTMQljn0?autoplay=1&rel=0&modestbranding=1';
    iframe.title = 'الفيديو التعريفي - المنصة التعليمية لتحفيظ القرآن الكريم';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    iframe.allowFullscreen = true;
    iframe.setAttribute('loading', 'lazy');
    
    placeholder.classList.add('hidden');
    wrapper.appendChild(iframe);
    videoLoaded = true;
    wrapper.onclick = null;
    // Error handling
    iframe.onerror = function() {
        wrapper.innerHTML = `
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: white;
                font-family: Arial, sans-serif;
            ">
                <h3>Video Unavailable</h3>
                <p>This video may be private or deleted.</p>
            </div>
        `;
    };
    
    // Remove placeholder and add iframe
    placeholder.remove();
    wrapper.appendChild(iframe);
    
    // Remove click handler
    wrapper.onclick = null;
}