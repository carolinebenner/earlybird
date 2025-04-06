/* Hero Logo Animation Script */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on the homepage
    if (window.location.pathname === '/' || window.location.pathname === '') {
        // Add homepage class to body
        document.body.classList.add('is-homepage');
        
        // Create the hero logo section element
        const heroSection = document.createElement('div');
        heroSection.id = 'hero-logo-section';
        
        // Create particles container
        const particlesContainer = document.createElement('div');
        particlesContainer.id = 'particles-hero';
        heroSection.appendChild(particlesContainer);
        
        // Create logo element
        const logoImg = document.createElement('img');
        logoImg.id = 'hero-logo';
        logoImg.src = document.querySelector('.navbar-brand img').src;
        logoImg.alt = 'Early Bird Logo';
        logoImg.style.maxWidth = '80%';
        logoImg.style.maxHeight = '60vh';
        heroSection.appendChild(logoImg);
        
        // Insert the hero section at the beginning of the body, before all content
        const mainContent = document.querySelector('.main-content');
        document.body.insertBefore(heroSection, mainContent);
        
        // Get the navbar element and navbar logo
        const navbar = document.querySelector('.navbar');
        const navbarLogo = navbar.querySelector('.navbar-brand img');
        navbar.id = 'mainNav';
        
        // Store the original navbar logo size
        const originalNavLogoHeight = parseInt(window.getComputedStyle(navbarLogo).height);
        
        // Initially make navbar transparent
        navbar.classList.add('top');
        navbar.style.backgroundColor = 'transparent';
        navbar.style.boxShadow = 'none';
        navbar.style.position = 'fixed';
        navbar.style.top = '0';
        navbar.style.width = '100%';
        navbar.style.zIndex = '1000';
        
        // Add GPU acceleration to smooth transitions
        heroSection.style.transform = 'translateZ(0)';
        logoImg.style.transform = 'translateZ(0)';
        
        // Make main content fade in after scroll
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(30px)';
        mainContent.classList.add('content-wrapper');
        
        // Add fade-in classes to hero section content
        const heroTitle = document.querySelector('.hero-title');
        const heroSubtitle = document.querySelector('.hero-subtitle');
        const heroButtons = document.querySelector('.hero-content .d-flex');
        
        if (heroTitle) heroTitle.classList.add('fade-in-delay-1');
        if (heroSubtitle) heroSubtitle.classList.add('fade-in-delay-2');
        if (heroButtons) heroButtons.classList.add('fade-in-delay-3');
        
        // Variables for smooth scrolling
        let lastScrollY = window.scrollY;
        let ticking = false;
        
        // Function to handle scroll effect with debouncing
        function handleScroll() {
            const scrollPosition = window.scrollY;
            const windowHeight = window.innerHeight;
            
            // Use requestAnimationFrame for smoother animations
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    // Calculate scroll percentage (0 to 1)
                    const scrollPercentage = Math.min(scrollPosition / (windowHeight * 0.6), 1);
                    
                    // Adjust hero section height and opacity
                    heroSection.style.height = `${Math.max(100 - scrollPercentage * 100, 0)}vh`;
                    heroSection.style.opacity = Math.max(1 - scrollPercentage * 1.5, 0);
                    
                    // Scale logo based on scroll with GPU acceleration
                    const logoScale = Math.max(1 - scrollPercentage * 0.7, 0.3);
                    logoImg.style.transform = `scale(${logoScale}) translateZ(0)`;
                    
                    // Increase navbar logo size when scrolled
                    if (scrollPercentage > 0.7) {
                        // When hero is almost gone, make navbar logo bigger
                        const newLogoHeight = originalNavLogoHeight * 1.4; // 40% bigger
                        navbarLogo.style.height = `${newLogoHeight}px`;
                        navbarLogo.style.transition = 'height 0.3s ease';
                    } else {
                        // Reset to original size when at top
                        navbarLogo.style.height = `${originalNavLogoHeight}px`;
                    }
                    
                    // Fade in navbar background after scrolling a bit
                    if (scrollPercentage > 0.1) {
                        navbar.classList.add('scrolled');
                        navbar.classList.remove('top');
                    } else {
                        navbar.classList.remove('scrolled');
                        navbar.classList.add('top');
                    }
                    
                    // Show main content when hero section starts to shrink
                    if (scrollPercentage > 0.3) {
                        mainContent.style.opacity = '1';
                        mainContent.style.transform = 'translateY(0)';
                    }
                    
                    // Hide hero section completely when fully scrolled
                    if (scrollPercentage >= 1) {
                        heroSection.classList.add('hero-hidden');
                    } else {
                        heroSection.classList.remove('hero-hidden');
                    }
                    
                    ticking = false;
                });
                
                ticking = true;
            }
            
            lastScrollY = scrollPosition;
        }
        
        // Initial call to set positions
        handleScroll();
        
        // Add scroll event listener with passive option for better performance
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Initialize particles for hero section
        if (typeof particlesJS !== 'undefined') {
            particlesJS("particles-hero", {
                "particles": {
                    "number": {
                        "value": 60, // Reduced particle count for better performance
                        "density": {
                            "enable": true,
                            "value_area": 800
                        }
                    },
                    "color": {
                        "value": "#6d5bec"
                    },
                    "shape": {
                        "type": "circle",
                        "stroke": {
                            "width": 0,
                            "color": "#000000"
                        },
                        "polygon": {
                            "nb_sides": 5
                        }
                    },
                    "opacity": {
                        "value": 0.5,
                        "random": false,
                        "anim": {
                            "enable": false,
                            "speed": 1,
                            "opacity_min": 0.1,
                            "sync": false
                        }
                    },
                    "size": {
                        "value": 3,
                        "random": true,
                        "anim": {
                            "enable": false,
                            "speed": 40,
                            "size_min": 0.1,
                            "sync": false
                        }
                    },
                    "line_linked": {
                        "enable": true,
                        "distance": 150,
                        "color": "#8f6afd",
                        "opacity": 0.4,
                        "width": 1
                    },
                    "move": {
                        "enable": true,
                        "speed": 2,
                        "direction": "none",
                        "random": false,
                        "straight": false,
                        "out_mode": "out",
                        "bounce": false,
                        "attract": {
                            "enable": false,
                            "rotateX": 600,
                            "rotateY": 1200
                        }
                    }
                },
                "interactivity": {
                    "detect_on": "canvas",
                    "events": {
                        "onhover": {
                            "enable": true,
                            "mode": "grab"
                        },
                        "onclick": {
                            "enable": true,
                            "mode": "push"
                        },
                        "resize": true
                    },
                    "modes": {
                        "grab": {
                            "distance": 140,
                            "line_linked": {
                                "opacity": 1
                            }
                        },
                        "bubble": {
                            "distance": 400,
                            "size": 40,
                            "duration": 2,
                            "opacity": 8,
                            "speed": 3
                        },
                        "repulse": {
                            "distance": 200,
                            "duration": 0.4
                        },
                        "push": {
                            "particles_nb": 4
                        },
                        "remove": {
                            "particles_nb": 2
                        }
                    }
                },
                "retina_detect": true
            });
        }
    }
});
