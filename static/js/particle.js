/**
 * Particles Configuration
 * This script initializes the particle animation in the background
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the current theme
    const isDarkTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    // Configure particles based on theme
    const particlesConfig = {
        particles: {
            number: {
                value: 80,
                density: {
                    enable: true,
                    value_area: 800
                }
            },
            color: {
                value: isDarkTheme ? "#4361ee" : "#4361ee"
            },
            shape: {
                type: "circle",
                stroke: {
                    width: 0,
                    color: "#000000"
                },
                polygon: {
                    nb_sides: 5
                }
            },
            opacity: {
                value: 0.4,
                random: false,
                anim: {
                    enable: false,
                    speed: 1,
                    opacity_min: 0.1,
                    sync: false
                }
            },
            size: {
                value: 3,
                random: true,
                anim: {
                    enable: false,
                    speed: 40,
                    size_min: 0.1,
                    sync: false
                }
            },
            line_linked: {
                enable: true,
                distance: 150,
                color: isDarkTheme ? "#667eea" : "#4361ee",
                opacity: 0.2,
                width: 1
            },
            move: {
                enable: true,
                speed: 2,
                direction: "none",
                random: false,
                straight: false,
                out_mode: "out",
                bounce: false,
                attract: {
                    enable: false,
                    rotateX: 600,
                    rotateY: 1200
                }
            }
        },
        interactivity: {
            detect_on: "canvas",
            events: {
                onhover: {
                    enable: true,
                    mode: "grab"
                },
                onclick: {
                    enable: true,
                    mode: "push"
                },
                resize: true
            },
            modes: {
                grab: {
                    distance: 140,
                    line_linked: {
                        opacity: 0.8
                    }
                },
                bubble: {
                    distance: 400,
                    size: 40,
                    duration: 2,
                    opacity: 8,
                    speed: 3
                },
                repulse: {
                    distance: 200,
                    duration: 0.4
                },
                push: {
                    particles_nb: 4
                },
                remove: {
                    particles_nb: 2
                }
            }
        },
        retina_detect: true
    };

    // Initialize particles
    if (document.getElementById('particles-js')) {
        particlesJS('particles-js', particlesConfig);
    }

    // Listen for theme changes to update particles
    document.addEventListener('theme-changed', function(e) {
        const isDark = e.detail.theme === 'dark';
        
        if (window.pJSDom && window.pJSDom[0]) {
            // Update particle colors based on new theme
            window.pJSDom[0].pJS.particles.color.value = isDark ? "#4361ee" : "#4361ee";
            window.pJSDom[0].pJS.particles.line_linked.color = isDark ? "#667eea" : "#4361ee";
            
            // Refresh particles
            window.pJSDom[0].pJS.fn.particlesRefresh();
        }
    });
});
