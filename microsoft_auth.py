"""
Microsoft OAuth Authentication Blueprint

This module handles the Microsoft/Outlook authentication process
and integration with Outlook Calendar.
"""

import json
import os
from urllib.parse import urlencode

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

# Microsoft OAuth configuration
MS_CLIENT_ID = os.environ.get("MICROSOFT_OAUTH_CLIENT_ID")
MS_CLIENT_SECRET = os.environ.get("MICROSOFT_OAUTH_CLIENT_SECRET")
MS_AUTHORITY = "https://login.microsoftonline.com/common"
MS_AUTH_ENDPOINT = f"{MS_AUTHORITY}/oauth2/v2.0/authorize"
MS_TOKEN_ENDPOINT = f"{MS_AUTHORITY}/oauth2/v2.0/token"
MS_GRAPH_API = "https://graph.microsoft.com/v1.0"

# Define required scopes - email profile and calendar access
SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",  # For refresh tokens
    "Calendars.ReadWrite",  # Permission to read/write calendar
]

# Set up the client
client = WebApplicationClient(MS_CLIENT_ID) if MS_CLIENT_ID else None

# Create the Blueprint
microsoft_auth = Blueprint("microsoft_auth", __name__)


@microsoft_auth.before_request
def check_ms_configuration():
    """Check if Microsoft OAuth is configured."""
    global client
    if not MS_CLIENT_ID or not MS_CLIENT_SECRET:
        current_app.logger.warning(
            "Microsoft OAuth is not configured. Please set MICROSOFT_OAUTH_CLIENT_ID "
            "and MICROSOFT_OAUTH_CLIENT_SECRET environment variables."
        )
        if not client and MS_CLIENT_ID:
            client = WebApplicationClient(MS_CLIENT_ID)


@microsoft_auth.route("/microsoft_login")
def login():
    """Generate Microsoft login URL and redirect to Microsoft's OAuth consent screen"""
    if not MS_CLIENT_ID or not client:
        return "Microsoft OAuth Client ID not set. Please configure the application.", 500

    # Get the redirect URI
    redirect_uri = request.base_url.replace("http://", "https://") + "/callback"
    
    # Create authorization URL
    auth_url = client.prepare_request_uri(
        MS_AUTH_ENDPOINT,
        redirect_uri=redirect_uri,
        scope=" ".join(SCOPES),
        response_type="code",
        prompt="select_account",  # Force account selection
    )
    
    # Redirect to Microsoft login
    return redirect(auth_url)


@microsoft_auth.route("/microsoft_login/callback")
def callback():
    """Handle the callback from Microsoft OAuth server"""
    if not MS_CLIENT_ID or not MS_CLIENT_SECRET:
        return "Microsoft OAuth not configured. Please set the environment variables.", 500

    # Get authorization code
    code = request.args.get("code")
    if not code:
        return "Authentication failed: No authorization code received.", 400

    # Get the redirect URI
    redirect_uri = request.base_url.replace("http://", "https://")
    
    # Prepare the token request
    token_url, headers, body = client.prepare_token_request(
        MS_TOKEN_ENDPOINT,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=redirect_uri,
        code=code,
    )
    
    # Send the token request
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(MS_CLIENT_ID, MS_CLIENT_SECRET),
    )
    
    # Parse the token response
    token_data = token_response.json()
    if "error" in token_data:
        return f"Error obtaining token: {token_data['error']}", 400
    
    # Store tokens
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # Get user information from Microsoft Graph API
    user_info_url = f"{MS_GRAPH_API}/me"
    user_info_response = requests.get(
        user_info_url, 
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    user_info = user_info_response.json()
    
    # Get user email and name
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    name = user_info.get("displayName") or email.split("@")[0]
    
    if not email:
        return "Couldn't retrieve email from Microsoft. Access denied.", 400
    
    # Look up user in database, or create if new
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=name, email=email)
        db.session.add(user)
    
    # Save the MS token for later use with calendar operations
    user.microsoft_token = json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_at": token_data.get("expires_in"),
    })
    
    db.session.commit()
    
    # Log the user in
    login_user(user)
    
    return redirect(url_for("index"))


@microsoft_auth.route("/microsoft_logout")
@login_required
def logout():
    """Logout user from Microsoft (just clears local token)"""
    if current_user.is_authenticated and current_user.microsoft_token:
        current_user.microsoft_token = None
        db.session.commit()
    
    return redirect(url_for("logout"))


def add_event_to_outlook_calendar(event_data):
    """
    Add an event to the user's Outlook Calendar
    
    Args:
        event_data (dict): A dictionary containing event information:
            - start_time: datetime object for the event start
            - end_time: datetime object for the event end
            - title: Event title
            - description: Event description
            
    Returns:
        tuple: (success, message) where success is a boolean and message is a string
    """
    if not current_user.is_authenticated or not current_user.microsoft_token:
        return False, "User not authenticated with Microsoft"
    
    # Parse stored token
    try:
        token_data = json.loads(current_user.microsoft_token)
        access_token = token_data.get("access_token")
    except Exception as e:
        return False, f"Error parsing token: {str(e)}"
    
    # Format the event data for Microsoft Graph API
    # ISO 8601 format with timezone info
    if not event_data.get("start_time") or not event_data.get("end_time"):
        return False, "Start time and end time are required"
    
    start_iso = event_data["start_time"].strftime("%Y-%m-%dT%H:%M:%S")
    end_iso = event_data["end_time"].strftime("%Y-%m-%dT%H:%M:%S")
    
    event = {
        "subject": event_data.get("title", "New Event"),
        "body": {
            "contentType": "text",
            "content": event_data.get("description", "")
        },
        "start": {
            "dateTime": start_iso,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": "UTC"
        }
    }
    
    # Add location if provided
    if "location" in event_data and event_data["location"]:
        event["location"] = {
            "displayName": event_data["location"]
        }
    
    # Add the event to the user's calendar
    endpoint = f"{MS_GRAPH_API}/me/calendar/events"
    
    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=event
        )
        
        # Check response
        if response.status_code == 201:
            return True, "Event successfully added to Outlook Calendar"
        else:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            return False, f"Failed to add event: {error_message}"
            
    except Exception as e:
        return False, f"Error adding event to Outlook Calendar: {str(e)}"


def refresh_microsoft_token():
    """
    Refresh the Microsoft access token using the refresh token
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not current_user.is_authenticated or not current_user.microsoft_token:
        return False
    
    try:
        token_data = json.loads(current_user.microsoft_token)
        refresh_token = token_data.get("refresh_token")
        
        if not refresh_token:
            return False
        
        # Prepare the refresh token request
        refresh_url = MS_TOKEN_ENDPOINT
        data = {
            "client_id": MS_CLIENT_ID,
            "client_secret": MS_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        response = requests.post(refresh_url, data=data)
        
        if response.status_code == 200:
            new_token_data = response.json()
            
            # Update stored token
            current_user.microsoft_token = json.dumps({
                "access_token": new_token_data.get("access_token"),
                "refresh_token": new_token_data.get("refresh_token", refresh_token),
                "token_type": "Bearer",
                "expires_at": new_token_data.get("expires_in"),
            })
            
            db.session.commit()
            return True
        else:
            return False
            
    except Exception:
        return False