/**
 * Paper to Calendar Animation
 * This script handles the animation of transforming a paper document 
 * into a calendar after file upload
 */

document.addEventListener('DOMContentLoaded', function() {
    // Reference to the animation container
    const animationContainer = document.getElementById('animation-container');
    
    if (!animationContainer) return;
    
    // Create the paper document element
    const createPaperDocument = () => {
        const paper = document.createElement('div');
        paper.className = 'paper-document';
        
        // Add some fake lines to simulate text
        for (let i = 0; i < 8; i++) {
            const line = document.createElement('div');
            line.className = i % 3 === 0 ? 'paper-line short' : 'paper-line';
            paper.appendChild(line);
        }
        
        return paper;
    };
    
    // Create a calendar element
    const createCalendar = () => {
        const calendar = document.createElement('div');
        calendar.className = 'calendar-result';
        
        // Calendar header with month
        const header = document.createElement('div');
        header.className = 'calendar-header';
        
        const monthName = document.createElement('div');
        monthName.className = 'calendar-month';
        monthName.textContent = 'April 2025';
        header.appendChild(monthName);
        calendar.appendChild(header);
        
        // Weekday labels
        const weekdays = document.createElement('div');
        weekdays.className = 'calendar-days';
        const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
        days.forEach(day => {
            const weekday = document.createElement('div');
            weekday.className = 'calendar-weekday';
            weekday.textContent = day;
            weekdays.appendChild(weekday);
        });
        calendar.appendChild(weekdays);
        
        // Calendar grid
        const calGrid = document.createElement('div');
        calGrid.className = 'calendar-days';
        
        // Create empty days for padding
        for (let i = 0; i < 2; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day';
            calGrid.appendChild(emptyDay);
        }
        
        // Calendar days with some event highlights
        const eventDays = [10, 15, 22];
        for (let i = 1; i <= 30; i++) {
            const day = document.createElement('div');
            day.className = eventDays.includes(i) ? 'calendar-day event' : 'calendar-day';
            day.textContent = i;
            calGrid.appendChild(day);
        }
        
        calendar.appendChild(calGrid);
        return calendar;
    };
    
    // Initial state - show paper document
    let paperDoc = createPaperDocument();
    animationContainer.appendChild(paperDoc);
    
    // Function to trigger animation when file is uploaded
    window.animatePaperToCalendar = function() {
        if (!paperDoc) return;
        
        // Add animation class
        paperDoc.classList.add('animate-paper-to-calendar');
        
        // Replace with calendar at the mid-point of animation
        setTimeout(() => {
            animationContainer.innerHTML = ''; // Clear container
            const calendar = createCalendar();
            animationContainer.appendChild(calendar);
        }, 750); // Half of the 1.5s animation duration
    };
    
    // Listen for form submission to trigger animation
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (document.getElementById('file').files.length > 0) {
                window.animatePaperToCalendar();
            }
        });
    }
    
    // Also trigger on file input change
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                // Change button text to show selected file
                const fileName = this.files[0].name;
                const buttonText = document.querySelector('.file-upload-btn span');
                if (buttonText) {
                    buttonText.textContent = fileName.length > 20 ? 
                        fileName.substring(0, 17) + '...' : fileName;
                }
            }
        });
    }
});

// Handle dropzone effects
function setupDropzone() {
    const dropzone = document.querySelector('.dropzone');
    if (!dropzone) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropzone.classList.add('dropzone-active');
    }
    
    function unhighlight() {
        dropzone.classList.remove('dropzone-active');
    }
    
    dropzone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const fileInput = document.getElementById('file');
            fileInput.files = files;
            
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
            
            // Update button text
            const fileName = files[0].name;
            const buttonText = document.querySelector('.file-upload-btn span');
            if (buttonText) {
                buttonText.textContent = fileName.length > 20 ? 
                    fileName.substring(0, 17) + '...' : fileName;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', setupDropzone);
