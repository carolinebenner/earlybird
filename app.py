import os
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, session

from document_parser import extract_text_from_file
from date_extractor import extract_dates_from_text, extract_event_metadata
from calendar_generator import create_ics_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure upload folder
UPLOAD_FOLDER = './uploads'
CALENDAR_FOLDER = './calendar_events'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CALENDAR_FOLDER'] = CALENDAR_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CALENDAR_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render index page with file upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process it for dates."""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file
        file.save(file_path)
        
        try:
            # Extract text from file
            document_text = extract_text_from_file(file_path)
            
            # Extract dates from text
            min_confidence = float(request.form.get('min_confidence', 0.5))
            date_results = extract_dates_from_text(document_text)
            
            # Filter dates by confidence
            filtered_dates = [
                (date_str, date_obj, confidence, idx) 
                for idx, (date_str, date_obj, confidence) in enumerate(date_results)
                if confidence >= min_confidence
            ]
            
            if not filtered_dates:
                flash('No dates found with sufficient confidence', 'warning')
                return redirect(url_for('index'))
            
            # Prepare events preview data
            events_preview = []
            for date_str, date_obj, confidence, idx in filtered_dates:
                # Find position of date in text
                pos = document_text.find(date_str)
                
                # Extract potential event title and context
                title, description = extract_event_metadata(document_text, pos)
                
                event_info = {
                    'id': idx,
                    'date_str': date_str,
                    'date_obj_str': date_obj.isoformat(),  # Convert to string for session storage
                    'confidence': confidence,
                    'title': title or f"Event on {date_obj.strftime('%Y-%m-%d')}",
                    'full_description': description,
                    'description': document_text[max(0, pos - 100):min(len(document_text), pos + 100)]
                }
                
                events_preview.append(event_info)
            
            # Store in session for the preview page
            session['events_preview'] = events_preview
            session['document_text'] = document_text
            
            return render_template('preview.html', events=events_preview)
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash(f'Allowed file types are: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
        return redirect(url_for('index'))


@app.route('/generate', methods=['POST'])
def generate_calendar():
    if 'events_preview' not in session:
        flash('Session expired. Please upload the file again.', 'error')
        return redirect(url_for('index'))
    
    # Get selected events from form
    selected_events = request.form.getlist('selected_events', type=int)
    
    if not selected_events:
        flash('No events selected', 'warning')
        return redirect(url_for('index'))
    
    session_events = session.get('events_preview', [])
    document_text = session.get('document_text', '')
    
    created_files = []
    
    for event_id in selected_events:
        for session_event in session_events:
            if session_event['id'] == event_id:
                # Convert stored string datetime back to datetime object
                date_obj = datetime.strptime(session_event['date_obj_str'], '%Y-%m-%dT%H:%M:%S')
                
                # Additional form data for this event
                form_key = f'title_{event_id}'
                custom_title = request.form.get(form_key, session_event['title'])
                
                form_key = f'start_time_{event_id}'
                start_time_str = request.form.get(form_key)
                start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M') if start_time_str else date_obj
                
                form_key = f'end_time_{event_id}'
                end_time_str = request.form.get(form_key)
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M') if end_time_str else start_time + timedelta(hours=1)
                
                form_key = f'description_{event_id}'
                custom_description = request.form.get(form_key, session_event['full_description'])
                
                # Create event data
                event_data = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'title': custom_title,
                    'description': custom_description
                }
                
                # Create ICS file
                try:
                    filepath = create_ics_file(event_data, app.config['CALENDAR_FOLDER'])
                    created_files.append(os.path.basename(filepath))
                except Exception as e:
                    logger.error(f"Failed to create calendar event: {e}")
                    flash(f'Failed to create event: {str(e)}', 'error')
    
    # Clear session data
    session.clear()
    
    return render_template('download.html', files=created_files)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['CALENDAR_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)