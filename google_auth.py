import json
import os
import requests
from flask import Blueprint, redirect, request, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from oauthlib.oauth2 import WebApplicationClient
from datetime import datetime, timedelta
from app import db, login_manager
from models import User

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar.events"  # For adding events to calendar
]

# Make sure to use this redirect URL. It has to match the one in the whitelist
# Set the redirect URL directly with the current domain
# Since we're having issues with environment variables, we'll use a more direct approach
# to ensure the callback URL matches exactly what Google expects
DEV_REDIRECT_URL = 'https://a92c8796-5385-4590-872e-8108346143b3-00-3h1poy5pxr2sr.spock.replit.dev/google_login/callback'

# Always display setup instructions to the user
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. For OAuth consent screen settings:
   - Set User Type to External
   - Add your app name, support email, and developer contact information
   - Add the following scopes: .../auth/userinfo.email, .../auth/userinfo.profile, .../auth/calendar.events
4. Add the following Authorized redirect URI:
   {DEV_REDIRECT_URL}
5. Make sure to enable the Google Calendar API in the API Library

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Create blueprint for auth routes
google_auth = Blueprint("google_auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@google_auth.route("/google_login")
def login():
    """Generate Google login URL and redirect to Google's OAuth 2.0 consent screen"""
    # Find out what URL to hit for Google login
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Log the redirect URI for debugging
    callback_uri = DEV_REDIRECT_URL
    print(f"Using redirect URI: {callback_uri}")

    # Use library to construct the request for Google login
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=callback_uri,
        scope=SCOPES,
    )
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def callback():
    """Handle the callback from Google OAuth 2.0 server"""
    # Get authorization code Google sent back
    code = request.args.get("code")
    
    # Find out what URL to hit to get tokens
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Log the details for debugging
    print(f"Received callback with code: {code}")
    print(f"Using redirect URI: {DEV_REDIRECT_URL}")
    
    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=DEV_REDIRECT_URL,
        code=code
    )
    # Only use authentication if both client ID and secret are available
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
    else:
        # Fallback without authentication - will likely fail but avoids errors
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
        )

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Make sure email is verified with Google
    userinfo = userinfo_response.json()
    if not userinfo.get("email_verified"):
        return "User email not available or not verified by Google.", 400
    
    # Get user data
    google_id = userinfo["sub"]
    users_email = userinfo["email"]
    users_name = userinfo.get("given_name", users_email.split('@')[0])
    
    # Save token information 
    token_data = token_response.json()
    
    # Check if user exists
    user = User.query.filter_by(email=users_email).first()
    
    # If user doesn't exist, create new user
    if not user:
        user = User(username=users_name, email=users_email, google_token=json.dumps(token_data))
        db.session.add(user)
    else:
        # Update token
        user.google_token = json.dumps(token_data)
    
    db.session.commit()
    
    # Begin user session by logging the user in
    login_user(user)
    
    # Send user back to homepage
    return redirect(url_for("index"))

@google_auth.route("/logout")
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash("Successfully logged out", "success")
    return redirect(url_for("index"))

def add_event_to_google_calendar(event_data):
    """
    Add an event to the user's Google Calendar
    
    Args:
        event_data (dict): A dictionary containing event information:
            - start_time: datetime object for the event start
            - end_time: datetime object for the event end
            - title: Event title
            - description: Event description
            
    Returns:
        tuple: (success, message) where success is a boolean and message is a string
    """
    if not current_user.is_authenticated or not current_user.google_token:
        return False, "User not authenticated with Google"
    
    try:
        # Parse token from user record
        token_data = json.loads(current_user.google_token)
        
        # Check if token is expired
        if 'expires_at' in token_data and token_data['expires_at'] < datetime.now().timestamp():
            # Token is expired, try to refresh
            refresh_token = token_data.get('refresh_token')
            if not refresh_token:
                return False, "No refresh token available"
            
            # Refresh the token
            try:
                # Find out what URL to hit for token refresh
                google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
                token_endpoint = google_provider_cfg["token_endpoint"]
                
                # Prepare token refresh request
                refresh_request = {
                    'refresh_token': refresh_token,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'grant_type': 'refresh_token'
                }
                
                # Make the request
                try:
                    response = requests.post(token_endpoint, data=refresh_request)
                    if response.status_code != 200:
                        return False, "Failed to refresh token, please log in again"
                except Exception as conn_error:
                    return False, f"Could not connect to Google: {str(conn_error)}"
                
                # Update token data
                new_token_data = response.json()
                # Preserve the refresh token if not returned in the response
                if 'refresh_token' not in new_token_data and refresh_token:
                    new_token_data['refresh_token'] = refresh_token
                
                # Update user's token in database
                current_user.google_token = json.dumps(new_token_data)
                db.session.commit()
                
                # Use the new token
                token_data = new_token_data
            except Exception as e:
                return False, f"Error refreshing token: {str(e)}"
        
        # Create event data for Google Calendar API
        event = {
            'summary': event_data['title'],
            'description': event_data['description'],
            'start': {
                'dateTime': event_data['start_time'].strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event_data['end_time'].strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': 'UTC',
            },
        }
        
        # Add event to Google Calendar
        headers = {
            'Authorization': f"Bearer {token_data['access_token']}",
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            GOOGLE_CALENDAR_API_URL,
            headers=headers,
            json=event
        )
        
        if response.status_code == 200:
            return True, "Event added to Google Calendar successfully"
        else:
            return False, f"Failed to add event to Google Calendar: {response.text}"
            
    except Exception as e:
        return False, f"Error adding event to Google Calendar: {str(e)}"