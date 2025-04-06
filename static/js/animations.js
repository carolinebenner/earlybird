document.addEventListener('DOMContentLoaded', function() {
    // Dropzone functionality with animations
    const dropzone = document.querySelector('.dropzone');
    const fileInput = document.querySelector('.file-upload-btn input[type="file"]');
    const fileForm = document.getElementById('file-form');
    
    if (dropzone && fileInput) {
        // Prevent default behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight dropzone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropzone.style.transform = 'scale(1.05) translateY(-10px)';
            dropzone.style.boxShadow = '0 30px 60px rgba(0, 0, 0, 0.5)';
            dropzone.style.borderColor = 'rgba(59, 130, 246, 0.8)';
        }
        
        function unhighlight() {
            dropzone.style.transform = '';
            dropzone.style.boxShadow = '';
            dropzone.style.borderColor = '';
        }
        
        // Handle dropped files
        dropzone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                // Create ripple effect
                const rect = dropzone.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const ripple = document.createElement('div');
                ripple.classList.add('ripple');
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                dropzone.appendChild(ripple);
                
                // Remove ripple after animation
                setTimeout(() => {
                    ripple.remove();
                }, 600);
                
                // Show upload animation
                const uploadIcon = dropzone.querySelector('.upload-icon');
                uploadIcon.classList.add('uploading');
                
                // Set the file to the form input and submit
                fileForm.files = files;
                
                // Submit the main form
                const mainForm = document.querySelector('form[action*="upload_file"]');
                if (mainForm) {
                    const formInput = mainForm.querySelector('input[type="file"]');
                    if (formInput) {
                        formInput.files = files;
                        
                        // Wait for animation then submit
                        setTimeout(() => {
                            mainForm.submit();
                        }, 800);
                    }
                }
            }
        }
        
        // Click on dropzone redirects to file input
        dropzone.addEventListener('click', function() {
            fileInput.click();
        });
        
        // File input change animation
        fileInput.addEventListener('change', function() {
            if (this.files.length) {
                const uploadBtn = document.querySelector('.file-upload-btn');
                uploadBtn.classList.add('file-selected');
                setTimeout(() => {
                    // Auto-submit the form
                    this.form.submit();
                }, 500);
            }
        });
    }
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            width: 200px;
            height: 200px;
            margin-left: -100px;
            margin-top: -100px;
        }
        
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .uploading {
            animation: rotate 1.5s linear infinite;
        }
        
        .file-selected {
            background: var(--bs-primary) !important;
            color: white !important;
            animation: pulse 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
        }
    `;
    document.head.appendChild(style);
    
    // Make the steps follow the mouse subtly on hover
    const container = document.querySelector('.hero-section');
    if (container) {
        container.addEventListener('mousemove', (e) => {
            const cards = document.querySelectorAll('.floating-card, .step-item');
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            cards.forEach(card => {
                const cardX = (mouseX - 0.5) * 20;
                const cardY = (mouseY - 0.5) * 10;
                card.style.transform = `translate(${cardX}px, ${cardY}px)`;
            });
        });
    }
});
