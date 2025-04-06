import os
import json
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy.orm import DeclarativeBase

from document_parser import extract_text_from_file
from date_extractor import extract_dates_from_text, extract_event_metadata, extract_structured_events
from syllabus_extractor import extract_assessments_from_syllabus
from calendar_generator import create_ics_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask application and database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"
login_manager.login_message = "Please log in to access this feature"
login_manager.login_message_category = "info"

# Import models and create tables
with app.app_context():
    from models import User
    db.create_all()

# Import and register Google Auth blueprint
from google_auth import google_auth, add_event_to_google_calendar
app.register_blueprint(google_auth)

# Import and register Microsoft Auth blueprint
from microsoft_auth import microsoft_auth, add_event_to_outlook_calendar
app.register_blueprint(microsoft_auth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure upload folder
UPLOAD_FOLDER = './uploads'
CALENDAR_FOLDER = './calendar_events'
TEMP_FOLDER = './temp'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CALENDAR_FOLDER'] = CALENDAR_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_TYPE'] = 'filesystem'

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CALENDAR_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render index page with file upload form."""
    return render_template('index.html')


@app.route('/about')
def about():
    """Render about us page."""
    return render_template('about.html')

@app.route('/check-google-setup')
def check_google_setup():
    """Check Google OAuth setup status."""
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "Not set")
    client_secret_status = "Set" if os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") else "Not set"
    
    # Get current redirect URL
    from google_auth import DEV_REDIRECT_URL
    
    # Test connectivity to Google services
    google_connectivity = "Unknown"
    google_error = None
    try:
        import requests
        response = requests.get("https://accounts.google.com/.well-known/openid-configuration", timeout=5)
        if response.status_code == 200:
            google_connectivity = "Connected"
        else:
            google_connectivity = "Failed"
            google_error = f"Received status code {response.status_code} from Google"
    except Exception as e:
        google_connectivity = "Failed"
        google_error = str(e)
    
    setup_info = {
        "client_id_status": "Set" if client_id != "Not set" else "Not set",
        "client_secret_status": client_secret_status,
        "redirect_url": DEV_REDIRECT_URL,
        "google_connectivity": google_connectivity,
        "google_error": google_error
    }
    
    return render_template('check_setup.html', setup_info=setup_info)


@app.route('/check-microsoft-setup')
def check_microsoft_setup():
    """Check Microsoft OAuth setup status."""
    client_id = os.environ.get("MICROSOFT_OAUTH_CLIENT_ID", "Not set")
    client_secret_status = "Set" if os.environ.get("MICROSOFT_OAUTH_CLIENT_SECRET") else "Not set"
    
    # Get current domain for redirect URL
    redirect_uri = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}/microsoft_login/callback"
    
    # Test connectivity to Microsoft services
    ms_connectivity = "Unknown"
    ms_error = None
    try:
        import requests
        response = requests.get("https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration", timeout=5)
        if response.status_code == 200:
            ms_connectivity = "Connected"
        else:
            ms_connectivity = "Failed"
            ms_error = f"Received status code {response.status_code} from Microsoft"
    except Exception as e:
        ms_connectivity = "Failed"
        ms_error = str(e)
    
    setup_info = {
        "client_id_status": "Set" if client_id != "Not set" else "Not set",
        "client_secret_status": client_secret_status,
        "redirect_url": redirect_uri,
        "ms_connectivity": ms_connectivity,
        "ms_error": ms_error
    }
    
    return render_template('check_microsoft_setup.html', setup_info=setup_info)


@app.route('/microsoft-setup-detail')
def microsoft_setup_detail():
    """Display detailed Microsoft OAuth setup instructions."""
    replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    redirect_uri = f"https://{replit_domain}/microsoft_login/callback"
    
    return f"""
    <html>
    <head>
        <title>Microsoft OAuth Setup</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <style>
            .tab-content {
                padding: 1rem;
                border: 1px solid #666;
                border-top: none;
                border-radius: 0 0 0.25rem 0.25rem;
            }
            .code-block {
                background-color: #333;
                padding: 0.5rem;
                border-radius: 0.25rem;
                font-family: monospace;
                word-break: break-all;
            }
        </style>
    </head>
    <body class="container mt-5">
        <div class="card bg-dark text-light">
            <div class="card-header">
                <h2>Microsoft OAuth Setup Instructions</h2>
            </div>
            <div class="card-body">
                <ul class="nav nav-tabs" id="troubleshootingTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="redirect-tab" data-bs-toggle="tab" data-bs-target="#redirect" type="button" role="tab">Redirect URI</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="permissions-tab" data-bs-toggle="tab" data-bs-target="#permissions" type="button" role="tab">API Permissions</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="advanced-tab" data-bs-toggle="tab" data-bs-target="#advanced" type="button" role="tab">Advanced Settings</button>
                    </li>
                </ul>
                
                <div class="tab-content" id="troubleshootingTabsContent">
                    <!-- REDIRECT URI TAB -->
                    <div class="tab-pane fade show active" id="redirect" role="tabpanel">
                        <div class="alert alert-warning">
                            <strong>Error Detected:</strong> The Microsoft login is failing with "No reply address provided" or "invalid_request" errors.
                            This means the redirect URI in your Microsoft Azure App registration doesn't match the one our application is using.
                        </div>
                        
                        <h4>Follow these steps to set up the redirect URI:</h4>
                        <ol class="list-group list-group-numbered">
                            <li class="list-group-item bg-dark text-light">Sign in to the <a href="https://portal.azure.com/" target="_blank" class="text-info">Azure Portal</a></li>
                            <li class="list-group-item bg-dark text-light">Go to Azure Active Directory > App Registrations</li>
                            <li class="list-group-item bg-dark text-light">Find and select your application</li>
                            <li class="list-group-item bg-dark text-light">Click on "Authentication" in the left menu</li>
                            <li class="list-group-item bg-dark text-light">Under "Platform configurations", click "Add a platform" and select "Web"</li>
                            <li class="list-group-item bg-dark text-light">Add the following exact Redirect URI:
                                <div class="alert alert-info mt-2">
                                    <code class="code-block">{redirect_uri}</code>
                                    <button class="btn btn-sm btn-primary float-end" 
                                            onclick="navigator.clipboard.writeText('{redirect_uri}')">
                                        Copy
                                    </button>
                                </div>
                            </li>
                            <li class="list-group-item bg-dark text-light">Save your changes</li>
                        </ol>
                        
                        <div class="alert alert-info mt-4">
                            <h5>Important Notes:</h5>
                            <ul>
                                <li>The redirect URI must match exactly - including protocol (https://), domain, and path</li>
                                <li>Even a slight difference (such as missing trailing slash or extra spaces) will cause auth to fail</li>
                                <li>If you make changes, wait a few minutes for Azure to update before trying again</li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- API PERMISSIONS TAB -->
                    <div class="tab-pane fade" id="permissions" role="tabpanel">
                        <div class="alert alert-warning">
                            <strong>Error Detected:</strong> API permissions issues or "UnknownError" when accessing Microsoft Graph API.
                            This is typically due to missing or not-consented permissions.
                        </div>
                        
                        <h4>Follow these steps to fix the API permissions:</h4>
                        <ol class="list-group list-group-numbered">
                            <li class="list-group-item bg-dark text-light">Sign in to the <a href="https://portal.azure.com/" target="_blank" class="text-info">Azure Portal</a></li>
                            <li class="list-group-item bg-dark text-light">Go to Azure Active Directory > App Registrations</li>
                            <li class="list-group-item bg-dark text-light">Find and select your app</li>
                            <li class="list-group-item bg-dark text-light">Click on "API permissions" in the left sidebar</li>
                            <li class="list-group-item bg-dark text-light">Remove all existing permissions (click "..." next to each and select "Remove")</li>
                            <li class="list-group-item bg-dark text-light">Click "Add a permission"</li>
                            <li class="list-group-item bg-dark text-light">Select "Microsoft Graph"</li>
                            <li class="list-group-item bg-dark text-light">Select "Delegated permissions"</li>
                            <li class="list-group-item bg-dark text-light">
                                Add the following permissions:
                                <ul class="mt-2">
                                    <li><strong>User.Read</strong> (essential for profile access)</li>
                                    <li><strong>User.ReadBasic.All</strong></li>
                                    <li><strong>email</strong> (for email address access)</li>
                                    <li><strong>profile</strong> (for profile information)</li>
                                    <li><strong>openid</strong> (for authentication)</li>
                                    <li><strong>offline_access</strong> (for refresh tokens)</li>
                                    <li><strong>Calendars.ReadWrite</strong> (for calendar operations)</li>
                                </ul>
                            </li>
                            <li class="list-group-item bg-dark text-light bg-danger">
                                <strong>CRITICAL STEP:</strong> Click the "Grant admin consent for [your directory]" button at the top.
                                <div class="alert alert-danger mt-2">
                                    Without admin consent, the app can't access your profile data even with the right permissions.
                                </div>
                            </li>
                        </ol>
                        
                        <div class="alert alert-info mt-4">
                            <h5>Common Permission Issues:</h5>
                            <ul>
                                <li>The <strong>User.Read</strong> permission is essential - make sure it's added and consented</li>
                                <li>Microsoft's "email" scope is needed specifically to access the user's email address</li>
                                <li>You must grant admin consent after adding permissions</li>
                                <li>Permissions can take a few minutes to propagate after being added</li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- ADVANCED SETTINGS TAB -->
                    <div class="tab-pane fade" id="advanced" role="tabpanel">
                        <h4>Advanced Configuration Settings</h4>
                        
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5>Authentication Advanced Settings</h5>
                            </div>
                            <div class="card-body">
                                <ol class="list-group list-group-numbered">
                                    <li class="list-group-item bg-dark text-light">Go to "Authentication" in the left sidebar</li>
                                    <li class="list-group-item bg-dark text-light">
                                        Under "Implicit grant and hybrid flows", make sure both of these are checked:
                                        <ul class="mt-2">
                                            <li>Access tokens</li>
                                            <li>ID tokens</li>
                                        </ul>
                                    </li>
                                    <li class="list-group-item bg-dark text-light">
                                        Under "Advanced settings", ensure:
                                        <ul class="mt-2">
                                            <li>Allow public client flows: <strong>Yes</strong></li>
                                        </ul>
                                    </li>
                                </ol>
                            </div>
                        </div>
                        
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5>Verify Supported Account Types</h5>
                            </div>
                            <div class="card-body">
                                <p>Go to "Overview" in the left sidebar and verify the "Supported account types" setting:</p>
                                <div class="alert alert-info">
                                    Make sure it's set to <strong>"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"</strong>
                                </div>
                                <p>This setting allows both work/school accounts and personal Microsoft accounts to authenticate.</p>
                            </div>
                        </div>
                        
                        <div class="alert alert-info">
                            <h5>Debug Information:</h5>
                            <p>Current application redirect URI: <code class="code-block">{redirect_uri}</code></p>
                            <p>Microsoft Graph API endpoint: <code>https://graph.microsoft.com/v1.0/me</code></p>
                            <p>Server logs may contain more detailed error information.</p>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <a href="/" class="btn btn-primary">Return to Homepage</a>
                    <a href="/microsoft_login" class="btn btn-success ms-2">Try Microsoft Login Again</a>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JS Bundle with Popper -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    </body>
    </html>
    """


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
            
            # First try specialized syllabus assessment extractor for academic syllabi
            syllabus_events = extract_assessments_from_syllabus(document_text)
            
            # If syllabus-specific assessments found, use those
            structured_events = syllabus_events if syllabus_events else extract_structured_events(document_text)
            
            # Process events for display
            events_preview = []
            for idx, event in enumerate(structured_events):
                # We still need the original datetime object for the calendar
                # Try to parse the date from the structured event
                try:
                    date_obj = datetime.strptime(event['date'], '%Y-%m-%d')
                    
                    # Add time if available and in time format
                    if 'time' in event and ':' in event['time']:
                        time_parts = event['time'].split(':')
                        date_obj = date_obj.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
                    # Handle special cases like "during class" or "see course schedule"
                    elif 'time' in event:
                        # Use default time of 9:00 AM
                        date_obj = date_obj.replace(hour=9, minute=0)
                except ValueError:
                    # If date parsing fails, skip this event
                    continue
                
                # Format date for display
                date_formatted = date_obj.strftime('%Y-%m-%dT%H:%M')
                
                # Find this date in the text to get surrounding context
                date_str = event['date']
                pos = document_text.find(date_str)
                if pos == -1:
                    # If exact date format not found, try to find month/day
                    try:
                        month_name = date_obj.strftime('%B')
                        day = str(date_obj.day)
                        pos = document_text.find(f"{month_name} {day}")
                        if pos == -1:
                            pos = document_text.find(f"{month_name[:3]} {day}")
                    except:
                        pos = 0
                
                # No description as requested - we're removing descriptions to avoid confusion
                
                event_info = {
                    'id': idx,
                    'date_str': event['date'],
                    'date_obj_str': date_obj.isoformat(),  # Convert to string for storage
                    'date_formatted': date_formatted,
                    'confidence': 0.9,  # Higher default confidence for structured events
                    'title': event['title'],
                    'full_description': "",  # Empty description as requested
                    'description': ""  # Empty description as requested
                }
                
                events_preview.append(event_info)
            
            if not events_preview:
                # If no structured events were found, fall back to the original method
                date_results = extract_dates_from_text(document_text)
                
                # Process dates without filtering by confidence
                for idx, (date_str, date_obj, confidence) in enumerate(date_results):
                    # Find position of date in text
                    pos = document_text.find(date_str)
                    
                    # Extract potential event title and context
                    title, description = extract_event_metadata(document_text, pos)
                    
                    # Format date and time information for display and form
                    date_formatted = date_obj.strftime('%Y-%m-%dT%H:%M')
                    
                    event_info = {
                        'id': idx,
                        'date_str': date_str,
                        'date_obj_str': date_obj.isoformat(),
                        'date_formatted': date_formatted,
                        'confidence': confidence,
                        'title': title or f"Event on {date_obj.strftime('%Y-%m-%d')}",
                        'full_description': description,
                        'description': document_text[max(0, pos - 100):min(len(document_text), pos + 100)]
                    }
                    
                    events_preview.append(event_info)
                
                if not events_preview:
                    flash('No dates found in the document', 'warning')
                    return redirect(url_for('index'))
            
            # Generate a unique session ID
            session_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(filename) % 10000)
            
            # Store the data in a temporary file instead of in the session
            data = {
                'events_preview': events_preview,
                'document_text': document_text
            }
            
            temp_file_path = os.path.join(app.config['TEMP_FOLDER'], f"{session_id}.json")
            with open(temp_file_path, 'w') as f:
                json.dump(data, f)
            
            # Store only the session ID in the cookie
            session['session_id'] = session_id
            
            return render_template('preview.html', events=events_preview, session_id=session_id)
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash(f'Allowed file types are: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
        return redirect(url_for('index'))


@app.route('/generate', methods=['POST'])
def generate_calendar():
    # Get session ID from form
    session_id = request.form.get('session_id')
    
    if not session_id:
        flash('Session expired. Please upload the file again.', 'error')
        return redirect(url_for('index'))
    
    # Load data from temporary file
    temp_file_path = os.path.join(app.config['TEMP_FOLDER'], f"{session_id}.json")
    if not os.path.exists(temp_file_path):
        flash('Session data not found. Please upload the file again.', 'error')
        return redirect(url_for('index'))
    
    try:
        with open(temp_file_path, 'r') as f:
            data = json.load(f)
        
        session_events = data.get('events_preview', [])
        document_text = data.get('document_text', '')
    except Exception as e:
        logger.error(f"Failed to load session data: {e}")
        flash('Failed to load session data. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Get selected events from form
    selected_events = request.form.getlist('selected_events', type=int)
    
    if not selected_events:
        flash('No events selected', 'warning')
        return redirect(url_for('index'))
    
    created_files = []
    calendar_results = []
    add_to_google = request.form.get('add_to_google_calendar') == 'yes'
    add_to_outlook = request.form.get('add_to_outlook_calendar') == 'yes'
    
    for event_id in selected_events:
        for session_event in session_events:
            if session_event['id'] == event_id:
                try:
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
                    filepath = create_ics_file(event_data, app.config['CALENDAR_FOLDER'])
                    created_files.append(os.path.basename(filepath))
                    
                    # If user is logged in with Google and requested to add to Google Calendar
                    if add_to_google and current_user.is_authenticated and current_user.google_token:
                        success, message = add_event_to_google_calendar(event_data)
                        calendar_results.append({
                            'title': custom_title,
                            'success': success,
                            'message': message,
                            'calendar': 'Google'
                        })
                    
                    # If user is logged in with Microsoft and requested to add to Outlook Calendar
                    if add_to_outlook and current_user.is_authenticated and current_user.microsoft_token:
                        success, message = add_event_to_outlook_calendar(event_data)
                        calendar_results.append({
                            'title': custom_title,
                            'success': success,
                            'message': message,
                            'calendar': 'Outlook'
                        })
                
                except Exception as e:
                    logger.error(f"Failed to create calendar event: {e}")
                    flash(f'Failed to create event: {str(e)}', 'error')
    
    # Clean up - remove temporary file
    try:
        os.remove(temp_file_path)
    except Exception as e:
        logger.warning(f"Failed to remove temporary file: {e}")
    
    # Clear session data
    session.clear()
    
    # Determine which calendar services the user is connected to
    has_google = current_user.is_authenticated and current_user.google_token is not None
    has_outlook = current_user.is_authenticated and current_user.microsoft_token is not None
    
    return render_template('download.html', 
                          files=created_files, 
                          calendar_results=calendar_results,
                          is_authenticated=current_user.is_authenticated,
                          has_google=has_google,
                          has_outlook=has_outlook)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['CALENDAR_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)