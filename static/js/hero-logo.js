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
        
        // Initially hide navbar completely
        navbar.style.opacity = '0';
        navbar.style.transform = 'translateY(-100%)';
        navbar.style.position = 'fixed';
        navbar.style.top = '0';
        navbar.style.width = '100%';
        navbar.style.zIndex = '1000';
        navbar.style.transition = 'opacity 0.3s ease, transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease';
        
        // Add GPU acceleration to smooth transitions
        heroSection.style.transform = 'translateZ(0)';
        logoImg.style.transform = 'translateZ(0)';
        
        // Make main content fade in after scroll
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(30px)';
        mainContent.classList.add('content-wrapper');
        
        // Add fade-in classes to hero section content
        // Don't animate the hero title - let's keep it visible all times
        const heroSubtitle = document.querySelector('.hero-subtitle');
        const heroButtons = document.querySelector('.hero-content .d-flex');
        
        // No animation for title - keep it visible
        if (heroSubtitle) heroSubtitle.classList.add('fade-in-delay-2');
        if (heroButtons) heroButtons.classList.add('fade-in-delay-3');
        
        // Use animation frames to control smooth animations
        let lastScrollPosition = 0;
        let animationFrameId = null;
        
        // Function to update the animation based on scroll position
        function updateAnimation() {
            const scrollPosition = window.scrollY;
            const windowHeight = window.innerHeight;
            
            // Calculate scroll percentage (0 to 1)
            const scrollPercentage = Math.min(scrollPosition / (windowHeight * 0.6), 1);
            
            // Adjust hero section height and opacity
            heroSection.style.height = `${Math.max(100 - scrollPercentage * 100, 0)}vh`;
            heroSection.style.opacity = Math.max(1 - scrollPercentage * 1.5, 0);
            
            // Scale logo based on scroll with GPU acceleration
            const logoScale = Math.max(1 - scrollPercentage * 0.7, 0.3);
            logoImg.style.transform = `scale(${logoScale}) translateZ(0)`;
            
            // Show/hide navbar based on scroll position
            if (scrollPercentage > 0.2) {
                // Show navbar when scrolled a bit
                navbar.style.opacity = '1';
                navbar.style.transform = 'translateY(0)';
                navbar.style.backgroundColor = 'var(--nav-bg)';
                navbar.style.boxShadow = '0 2px 15px var(--shadow-color)';
                
                // When hero is almost gone, make navbar logo bigger
                if (scrollPercentage > 0.7) {
                    const newLogoHeight = originalNavLogoHeight * 1.4; // 40% bigger
                    navbarLogo.style.height = `${newLogoHeight}px`;
                    navbarLogo.style.transition = 'height 0.3s ease';
                    navbar.classList.add('scrolled');
                } else {
                    // Reset to original size when at mid-scroll
                    navbarLogo.style.height = `${originalNavLogoHeight}px`;
                    navbar.classList.remove('scrolled');
                }
            } else {
                // Hide navbar when at top
                navbar.style.opacity = '0';
                navbar.style.transform = 'translateY(-100%)';
                navbar.style.backgroundColor = 'transparent';
                navbar.style.boxShadow = 'none';
                navbar.classList.remove('scrolled');
            }
            
            // Show main content when hero section starts to shrink
            if (scrollPercentage > 0.3) {
                mainContent.style.opacity = '1';
                mainContent.style.transform = 'translateY(0)';
            } else {
                mainContent.style.opacity = '0';
                mainContent.style.transform = 'translateY(30px)';
            }
            
            // Hide hero section completely when fully scrolled
            if (scrollPercentage >= 1) {
                heroSection.classList.add('hero-hidden');
            } else {
                heroSection.classList.remove('hero-hidden');
            }
            
            // Store last position
            lastScrollPosition = scrollPosition;
        }
        
        // Use throttled scroll handler to avoid performance issues
        function handleScroll() {
            if (!animationFrameId) {
                animationFrameId = window.requestAnimationFrame(() => {
                    updateAnimation();
                    animationFrameId = null;
                });
            }
        }
        
        // Initial call to set positions
        updateAnimation();
        
        // Add scroll event listener with passive option for better performance
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Initialize particles for hero section only if the screen is large enough
        if (typeof particlesJS !== 'undefined' && window.innerWidth > 768) {
            particlesJS("particles-hero", {
                "particles": {
                    "number": {
                        "value": 40, // Reduced particle count for better performance
                        "density": {
                            "enable": true,
                            "value_area": 1000
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
                        "value": 0.4,
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
                        "opacity": 0.3,
                        "width": 1
                    },
                    "move": {
                        "enable": true,
                        "speed": 1.5,
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
                                "opacity": 0.8
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
