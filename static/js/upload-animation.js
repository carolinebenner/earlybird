// Animation script for document upload process

document.addEventListener('DOMContentLoaded', () => {
    // Animation elements
    let animationContainer = document.getElementById('animation-container');
    
    // Only proceed if we have the animation container
    if (!animationContainer) return;

    // Create animation elements
    setupAnimationElements();
    
    // File upload form handling
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                // Start animation when file is selected
                playUploadAnimation();
                
                // Submit the form after animation completes
                const form = e.target.closest('form');
                if (form) {
                    setTimeout(() => {
                        form.submit();
                    }, 3000); // 3 seconds total for both animations
                }
            }
        });
    });
    
    // Dropzone handling
    const dropzone = document.querySelector('.dropzone');
    if (dropzone) {
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dropzone-active');
        });
        
        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dropzone-active');
        });
        
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dropzone-active');
            
            const dt = e.dataTransfer;
            if (dt.files.length > 0) {
                // Set the file in the file input
                const fileInput = dropzone.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.files = dt.files;
                    
                    // Start animation
                    playUploadAnimation();
                    
                    // Submit the form after animation completes
                    const form = fileInput.closest('form');
                    if (form) {
                        setTimeout(() => {
                            form.submit();
                        }, 3000); // 3 seconds total for both animations
                    }
                }
            }
        });
    }
});

// Function to set up animation elements
function setupAnimationElements() {
    const animationContainer = document.getElementById('animation-container');
    if (!animationContainer) return;
    
    // Create paper document element
    const paperDocument = document.createElement('div');
    paperDocument.className = 'paper-document';
    paperDocument.id = 'paper-document';
    
    // Create calendar result element (initially hidden)
    const calendarResult = document.createElement('div');
    calendarResult.className = 'calendar-result d-none';
    calendarResult.id = 'calendar-result';
    
    // Add header to calendar
    const calendarHeader = document.createElement('div');
    calendarHeader.className = 'calendar-header';
    calendarHeader.textContent = 'Events Calendar';
    calendarResult.appendChild(calendarHeader);
    
    // Add body to calendar
    const calendarBody = document.createElement('div');
    calendarBody.className = 'calendar-body';
    
    // Add days of the week
    const daysOfWeek = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    daysOfWeek.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day day-header';
        dayElement.textContent = day;
        calendarBody.appendChild(dayElement);
    });
    
    // Add calendar grid cells
    for (let i = 1; i <= 31; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = i;
        
        // Randomly add event class to some days
        if (i % 5 === 0 || i % 7 === 0) {
            dayElement.classList.add('event');
            
            // Add a small event indicator
            const eventIndicator = document.createElement('div');
            eventIndicator.className = 'event-placeholder';
            dayElement.appendChild(eventIndicator);
        }
        
        calendarBody.appendChild(dayElement);
    }
    
    calendarResult.appendChild(calendarBody);
    
    // Add elements to animation container
    animationContainer.appendChild(paperDocument);
    animationContainer.appendChild(calendarResult);
}

// Function to play the upload animation
function playUploadAnimation() {
    const paperDocument = document.getElementById('paper-document');
    const calendarResult = document.getElementById('calendar-result');
    
    if (!paperDocument || !calendarResult) return;
    
    // Start paper crumpling animation
    paperDocument.classList.add('animate-crumple');
    
    // After crumpling animation completes, start transformation
    setTimeout(() => {
        paperDocument.classList.add('d-none');
        calendarResult.classList.remove('d-none');
        
        // Start calendar transformation animation
        calendarResult.classList.add('animate-transform');
    }, 1000); // 1 second for crumpling animation
}
