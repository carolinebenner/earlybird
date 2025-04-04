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
    # Use the correct Replit domain from environment variables
    replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    redirect_uri = f"https://{replit_domain}/microsoft_login/callback"
    
    # Log the redirectURI for debugging
    current_app.logger.info(f"Microsoft login redirect URI: {redirect_uri}")
    
    try:
        # Try to verify the Microsoft URL is accessible
        try:
            verify_response = requests.head(MS_AUTH_ENDPOINT, timeout=5)
            current_app.logger.info(f"MS Auth endpoint status: {verify_response.status_code}")
        except Exception as e:
            current_app.logger.error(f"Cannot connect to Microsoft auth endpoint: {str(e)}")
            return f"""
            <h1>Microsoft Authentication Service Unavailable</h1>
            <p>We're unable to connect to Microsoft's authentication service at this time.</p>
            <p>Error details: {str(e)}</p>
            <p><a href="{url_for('index')}">Return to the homepage</a></p>
            """, 503
            
        # Create authorization URL - Use simple string construction for debugging
        scope_str = " ".join(SCOPES)
        auth_url = f"{MS_AUTH_ENDPOINT}?client_id={MS_CLIENT_ID}&redirect_uri={redirect_uri}&scope={scope_str}&response_type=code&prompt=select_account"
        
        # Log the auth URL for debugging
        current_app.logger.info(f"Microsoft login URL: {auth_url}")
    except Exception as e:
        current_app.logger.error(f"Error creating Microsoft auth URL: {str(e)}")
        return f"Error creating Microsoft authentication URL: {str(e)}", 500
    
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

    # Get the redirect URI - use the same URI as in the login function
    replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    redirect_uri = f"https://{replit_domain}/microsoft_login/callback"
    
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
    try:
        token_data = token_response.json()
        current_app.logger.info(f"Microsoft token response status: {token_response.status_code}")
        current_app.logger.info(f"Microsoft token response data: {json.dumps(token_data)}")
        
        if "error" in token_data:
            error_msg = token_data.get('error')
            error_desc = token_data.get('error_description', '')
            current_app.logger.error(f"Error obtaining Microsoft token: {error_msg} - {error_desc}")
            
            # Return a more user-friendly error message with a link to the troubleshooting page
            return f"""
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Microsoft Authentication Error</h4>
                    <p>We couldn't complete your sign-in with Microsoft.</p>
                    <p><strong>Error:</strong> {error_msg}</p>
                    <p><strong>Details:</strong> {error_desc}</p>
                    <hr>
                    <p>This is often caused by incorrect redirect URI configuration in your Azure App.</p>
                    <a href="{url_for('microsoft_setup_detail')}" class="btn btn-warning">View Troubleshooting Guide</a>
                    <a href="{url_for('index')}" class="btn btn-primary">Return Home</a>
                </div>
            </div>
            """, 400
    except Exception as e:
        current_app.logger.error(f"Exception parsing Microsoft token response: {str(e)}")
        return f"An error occurred during Microsoft authentication: {str(e)}", 500
    
    # Store tokens
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # Get user information from Microsoft Graph API
    try:
        # First, try to decode information from the ID token instead of making an API call
        # This often works better with personal Microsoft accounts
        current_app.logger.info("Attempting to extract user info from ID token")
        id_token = token_data.get("id_token")
        
        if id_token:
            # The id_token is a JWT with three parts separated by dots
            try:
                # Get the payload part (second part) and decode it
                import base64
                import json
                
                # Split the token and get the payload part
                token_parts = id_token.split('.')
                if len(token_parts) >= 2:
                    # Fix padding for base64 decode
                    payload = token_parts[1]
                    payload += '=' * ((4 - len(payload) % 4) % 4)
                    
                    # Decode the payload
                    decoded_payload = base64.b64decode(payload)
                    token_info = json.loads(decoded_payload)
                    
                    current_app.logger.info(f"Successfully extracted user info from ID token: {json.dumps(token_info)}")
                    
                    # Use the token info as user info
                    user_info = token_info
                    user_info_response = type('obj', (object,), {'status_code': 200})  # Mock response object
                else:
                    current_app.logger.error("Invalid ID token format")
                    
                    # Fall back to API call
                    user_info_url = f"{MS_GRAPH_API}/me"
                    current_app.logger.info(f"Fallback: Requesting user info from {user_info_url}")
                    
                    user_info_response = requests.get(
                        user_info_url, 
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    current_app.logger.info(f"User info response status: {user_info_response.status_code}")
                    user_info = user_info_response.json()
            except Exception as e:
                current_app.logger.error(f"Error decoding ID token: {str(e)}")
                
                # Fall back to API call
                user_info_url = f"{MS_GRAPH_API}/me"
                current_app.logger.info(f"Fallback: Requesting user info from {user_info_url}")
                
                user_info_response = requests.get(
                    user_info_url, 
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                current_app.logger.info(f"User info response status: {user_info_response.status_code}")
                user_info = user_info_response.json()
        else:
            # No ID token, so use the API call
            user_info_url = f"{MS_GRAPH_API}/me"
            current_app.logger.info(f"Requesting user info from {user_info_url}")
            
            user_info_response = requests.get(
                user_info_url, 
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            current_app.logger.info(f"User info response status: {user_info_response.status_code}")
            user_info = user_info_response.json()
        
        # Log the user info for debugging
        current_app.logger.info(f"Microsoft user info response: {json.dumps(user_info)}")
        
        # Log request details for deeper debugging
        current_app.logger.info(f"Microsoft access token (first 20 chars): {access_token[:20]}...")
        current_app.logger.info(f"Token data: {json.dumps({k: v for k, v in token_data.items() if k != 'access_token' and k != 'refresh_token'})}")
        
        # Check for error in response
        if "error" in user_info:
            error_code = user_info.get("error", {}).get("code", "Unknown")
            error_message = user_info.get("error", {}).get("message", "Unknown error")
            inner_error = user_info.get("error", {}).get("innerError", {})
            current_app.logger.error(f"Error getting Microsoft user info: {error_code} - {error_message}")
            current_app.logger.error(f"Inner error details: {json.dumps(inner_error)}")
            
            # Let's try a different MS Graph endpoint to see if it's a specific endpoint issue
            try:
                test_endpoint = f"{MS_GRAPH_API}/me/memberOf"
                current_app.logger.info(f"Trying alternative endpoint: {test_endpoint}")
                test_response = requests.get(
                    test_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                current_app.logger.info(f"Alternative endpoint status: {test_response.status_code}")
                current_app.logger.info(f"Alternative endpoint response: {test_response.text[:200]}...")
            except Exception as e:
                current_app.logger.error(f"Error testing alternative endpoint: {str(e)}")
            
            return f"""
            <div class="container mt-5">
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Microsoft API Error</h4>
                    <p>We received an error from Microsoft when trying to get your profile information.</p>
                    <p><strong>Error:</strong> {error_code}</p>
                    <p><strong>Message:</strong> {error_message}</p>
                    <p><strong>Inner Error:</strong> {json.dumps(inner_error)}</p>
                    <hr>
                    <p>This is likely due to insufficient permissions or configuration issues. Please check:</p>
                    <ul>
                        <li>API permissions are properly granted (User.Read is essential)</li>
                        <li>Admin consent has been given for all permissions</li>
                        <li>Your app is registered as a Web platform</li>
                        <li>The redirect URI exactly matches: {request.base_url.replace("http://", "https://")}</li>
                    </ul>
                    <a href="{url_for('microsoft_setup_detail')}" class="btn btn-warning">View Troubleshooting Guide</a>
                    <a href="{url_for('index')}" class="btn btn-primary">Return Home</a>
                </div>
            </div>
            """, 400
    except Exception as e:
        current_app.logger.error(f"Exception getting Microsoft user info: {str(e)}")
        return f"An error occurred while retrieving your profile from Microsoft: {str(e)}", 500
    
    # Get user email and name
    email = user_info.get("mail") or user_info.get("userPrincipalName") or user_info.get("email") or user_info.get("preferred_username")
    
    # Add debug logging
    current_app.logger.info(f"Microsoft user info: {json.dumps(user_info)}")
    
    if not email:
        current_app.logger.error("Couldn't retrieve email from Microsoft. User info: " + json.dumps(user_info))
        error_message = """
        <div class="container mt-5">
            <div class="alert alert-danger">
                <h4 class="alert-heading">Microsoft Authentication Error</h4>
                <p>We couldn't retrieve your email address from Microsoft. This is required to create your account.</p>
                <hr>
                <p>This could be due to:</p>
                <ul>
                    <li>Missing required Microsoft Graph permissions</li>
                    <li>You didn't grant consent to access your email address</li>
                    <li>Your Microsoft account doesn't have an email address</li>
                </ul>
                <p>Please try again or use a different authentication method.</p>
                <a href="{}" class="btn btn-warning">Troubleshooting Guide</a>
                <a href="{}" class="btn btn-primary">Return Home</a>
            </div>
        </div>
        """.format(url_for('microsoft_setup_detail'), url_for('index'))
        return error_message, 400
    
    # Only try to split email if it exists
    name = user_info.get("displayName")
    if not name and email:
        name = email.split("@")[0]
    elif not name:
        name = "Microsoft User"  # Fallback username if neither displayName nor email is available
    
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