// Reviews Carousel - RTL with Auto-Loop and Smooth Transitions
(function() {
    'use strict';
    
    const reviews = [
        {file: 'review1.jpeg', alt: 'رأي طالب عن تجربته في تحفيظ القرآن'},
        {file: 'review2.jpeg', alt: 'تقييم ولي أمر لجودة التعليم'},
        {file: 'review3.jpeg', alt: 'شهادة طالبة عن تحسن مستواها'},
        {file: 'review4.jpeg', alt: 'رأي إيجابي عن المعلمات'},
        {file: 'review5.jpeg', alt: 'تجربة ناجحة في التحفيظ'},
        {file: 'review6.jpeg', alt: 'تقييم خمس نجوم'},
        {file: 'review7.jpeg', alt: 'شكر من ولي أمر'},
        {file: 'review8.jpeg', alt: 'رأي عن المواعيد المرنة'},
        {file: 'review9.jpeg', alt: 'تجربة في تصحيح التلاوة'},
        {file: 'review10.jpeg', alt: 'تقييم الدعم الفني'},
        {file: 'review11.jpeg', alt: 'فعالية البرامج التعليمية'},
        {file: 'review12.jpeg', alt: 'تطور سريع للطالب'}
    ];
    
    let currentPage = 0;
    let reviewsPerPage = 4;
    let totalPages = Math.ceil(reviews.length / reviewsPerPage);
    let autoPlayInterval;
    let imageObserver;
    let isInView = false;
    let sectionObserver;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        const reviewsGrid = document.getElementById('reviews-grid');
        if (!reviewsGrid) return;
        
        // Check if container already exists
        let container = reviewsGrid.closest('.reviews-container');
        
        if (!container) {
            // Wrap grid in container for navigation
            container = document.createElement('div');
            container.className = 'reviews-container';
            reviewsGrid.parentNode.insertBefore(container, reviewsGrid);
            container.appendChild(reviewsGrid);
        }
        
        // Remove any existing navigation elements
        const existingNavs = container.querySelectorAll('.carousel-nav');
        existingNavs.forEach(nav => nav.remove());
        
        const existingPagination = container.querySelector('.carousel-pagination');
        if (existingPagination) existingPagination.remove();
        
        // Update reviews per page based on screen size
        updateReviewsPerPage();
        window.addEventListener('resize', handleResize);
        
        // Create intersection observer for lazy loading images
        imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.getAttribute('data-src');
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        // Create intersection observer for section visibility (auto-play)
        const reviewsSection = document.querySelector('.reviews-section');
        if (reviewsSection) {
            sectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    isInView = entry.isIntersecting;
                    if (isInView) {
                        startAutoPlay();
                    } else {
                        stopAutoPlay();
                    }
                });
            }, {
                threshold: 0.3
            });
            
            sectionObserver.observe(reviewsSection);
        }
        
        // Create navigation arrows
        createNavigationArrows(container);
        
        // Create pagination dots
        createPagination(container);
        
        // Display first page
        displayPage(currentPage);
        
        // Start auto-play if section is in view
        if (isInView) {
            startAutoPlay();
        }
    }
    
    function updateReviewsPerPage() {
        const width = window.innerWidth;
        
        if (width <= 600) {
            reviewsPerPage = 1;
        } else if (width <= 900) {
            reviewsPerPage = 2;
        } else if (width <= 1200) {
            reviewsPerPage = 3;
        } else {
            reviewsPerPage = 4;
        }
        
        totalPages = Math.ceil(reviews.length / reviewsPerPage);
        
        // Adjust current page if necessary
        if (currentPage >= totalPages) {
            currentPage = totalPages - 1;
        }
    }
    
    function handleResize() {
        const oldReviewsPerPage = reviewsPerPage;
        updateReviewsPerPage();
        
        if (oldReviewsPerPage !== reviewsPerPage) {
            // Recreate pagination
            const oldPagination = document.getElementById('carousel-pagination');
            if (oldPagination) {
                oldPagination.remove();
            }
            
            const container = document.querySelector('.reviews-container');
            createPagination(container);
            displayPage(currentPage);
        }
    }
    
    function createNavigationArrows(container) {
        // Previous arrow (on the right for RTL - goes backward)
        const prevNav = document.createElement('div');
        prevNav.className = 'carousel-nav prev';
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '←';
        prevBtn.setAttribute('aria-label', 'السابق');
        prevBtn.onclick = () => {
            prevPage();
            resetAutoPlay();
        };
        prevNav.appendChild(prevBtn);
        
        // Next arrow (on the left for RTL - goes forward)
        const nextNav = document.createElement('div');
        nextNav.className = 'carousel-nav next';
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '→';
        nextBtn.setAttribute('aria-label', 'التالي');
        nextBtn.onclick = () => {
            nextPage();
            resetAutoPlay();
        };
        nextNav.appendChild(nextBtn);
        
        container.appendChild(prevNav);
        container.appendChild(nextNav);
    }
    
    function createPagination(container) {
        const pagination = document.createElement('div');
        pagination.className = 'carousel-pagination';
        pagination.id = 'carousel-pagination';
        
        for (let i = 0; i < totalPages; i++) {
            const dot = document.createElement('button');
            dot.className = 'pagination-dot';
            dot.setAttribute('aria-label', `الصفحة ${i + 1}`);
            if (i === currentPage) dot.classList.add('active');
            dot.onclick = () => {
                goToPage(i);
                resetAutoPlay();
            };
            pagination.appendChild(dot);
        }
        
        container.appendChild(pagination);
    }
    
    function displayPage(pageIndex) {
        const reviewsGrid = document.getElementById('reviews-grid');
        if (!reviewsGrid) return;
        
        // Fade out
        reviewsGrid.style.opacity = '0';
        
        setTimeout(() => {
            const startIdx = pageIndex * reviewsPerPage;
            const endIdx = Math.min(startIdx + reviewsPerPage, reviews.length);
            const pageReviews = reviews.slice(startIdx, endIdx);
            
            // Clear grid
            reviewsGrid.innerHTML = '';
            
            // Add reviews
            pageReviews.forEach((review, index) => {
                const globalIndex = startIdx + index;
                const reviewItem = createReviewItem(review, globalIndex + 1, index);
                reviewsGrid.appendChild(reviewItem);
            });
            
            // Fade in
            setTimeout(() => {
                reviewsGrid.style.opacity = '1';
            }, 50);
            
            // Update pagination
            updatePagination(pageIndex);
        }, 300);
    }
    
    function createReviewItem(review, number, delayIndex) {
        const reviewItem = document.createElement('article');
        reviewItem.className = 'review-item';
        reviewItem.style.animationDelay = `${delayIndex * 0.1}s`;
        
        const reviewNumber = document.createElement('div');
        reviewNumber.className = 'review-number';
        reviewNumber.textContent = `#${number}`;
        
        const img = document.createElement('img');
        img.className = 'skeleton';
        img.setAttribute('data-src', `/static/images/${review.file}`);
        img.alt = review.alt;
        img.width = 300;
        img.height = 350;
        img.loading = 'lazy';
        
        // Error handling
        img.onerror = function() {
            this.onerror = null;
            this.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='350'%3E%3Crect fill='%231b3a70' width='300' height='350'/%3E%3Ctext fill='%234CAF50' font-family='Arial' font-size='20' x='50%25' y='50%25' text-anchor='middle' dominant-baseline='middle'%3Eرأي طالب ${number}%3C/text%3E%3C/svg%3E`;
            this.classList.remove('skeleton');
        };
        
        img.onload = function() {
            this.classList.remove('skeleton');
        };
        
        reviewItem.appendChild(reviewNumber);
        reviewItem.appendChild(img);
        
        imageObserver.observe(img);
        
        return reviewItem;
    }
    
    function updatePagination(activeIndex) {
        const dots = document.querySelectorAll('.pagination-dot');
        dots.forEach((dot, index) => {
            if (index === activeIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
    
    function nextPage() {
        currentPage = (currentPage + 1) % totalPages;
        displayPage(currentPage);
    }
    
    function prevPage() {
        currentPage = (currentPage - 1 + totalPages) % totalPages;
        displayPage(currentPage);
    }
    
    function goToPage(pageIndex) {
        currentPage = pageIndex;
        displayPage(currentPage);
    }
    
    function startAutoPlay() {
        if (!autoPlayInterval) {
            autoPlayInterval = setInterval(() => {
                if (isInView) {
                    nextPage();
                }
            }, 5000);
        }
    }
    
    function stopAutoPlay() {
        if (autoPlayInterval) {
            clearInterval(autoPlayInterval);
            autoPlayInterval = null;
        }
    }
    
    function resetAutoPlay() {
        stopAutoPlay();
        if (isInView) {
            startAutoPlay();
        }
    }
    
    // Pause auto-play on hover
    document.addEventListener('mouseover', (e) => {
        if (e.target.closest('.review-item') || e.target.closest('.carousel-nav')) {
            stopAutoPlay();
        }
    });
    
    document.addEventListener('mouseout', (e) => {
        if (e.target.closest('.review-item') || e.target.closest('.carousel-nav')) {
            if (isInView) {
                startAutoPlay();
            }
        }
    });
    
    // Stop auto-play when page is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoPlay();
        } else if (isInView) {
            startAutoPlay();
        }
    });
})();