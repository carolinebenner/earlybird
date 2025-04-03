"""
Calendar Generator Module

This module handles the creation of calendar invitation files (.ics) 
from extracted date information.
"""

import os
import uuid
import logging
from datetime import datetime, timedelta

from icalendar import Calendar, Event
from icalendar import vCalAddress, vText

logger = logging.getLogger(__name__)

def create_ics_file(event_data, output_dir=None):
    """
    Create an ICS file from event data.
    
    Args:
        event_data (dict): A dictionary containing event information:
            - start_time: datetime object for the event start
            - end_time: datetime object for the event end (optional)
            - title: Event title (optional)
            - description: Event description (optional)
            - location: Event location (optional)
        output_dir (str): Directory to save the ICS file (default: current directory)
            
    Returns:
        str: Path to the created ICS file
    """
    # Set default output directory
    if output_dir is None:
        output_dir = './calendar_events'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract event data with defaults
    start_time = event_data.get('start_time')
    if not start_time:
        raise ValueError("Event must have a start time")
    
    # Default end time is 1 hour after start time if not provided
    end_time = event_data.get('end_time')
    if not end_time:
        end_time = start_time + timedelta(hours=1)
    
    title = event_data.get('title', f"Event on {start_time.strftime('%Y-%m-%d')}")
    description = event_data.get('description', '')
    location = event_data.get('location', '')
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Date Extractor//AI Assistant//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    
    # Create event
    event = Event()
    event.add('summary', title)
    event.add('description', description)
    if location:
        event.add('location', location)
    
    # Add start and end times
    event.add('dtstart', start_time)
    event.add('dtend', end_time)
    
    # Add timestamp and unique ID
    event.add('dtstamp', datetime.now())
    event.add('uid', str(uuid.uuid4()))
    
    # Add event to calendar
    cal.add_component(event)
    
    # Generate filename: Date_Title.ics
    date_str = start_time.strftime('%Y%m%d')
    title_slug = '_'.join(title.split()[:3])  # Use first three words of title
    title_slug = ''.join(c if c.isalnum() else '_' for c in title_slug)  # Remove special chars
    filename = f"{date_str}_{title_slug}.ics"
    
    # Create a unique filename if it already exists
    base_path = os.path.join(output_dir, filename)
    file_path = base_path
    counter = 1
    
    while os.path.exists(file_path):
        file_path = os.path.join(output_dir, f"{date_str}_{title_slug}_{counter}.ics")
        counter += 1
    
    # Write to file
    with open(file_path, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Created calendar file: {file_path}")
    return file_path


def create_multiple_ics_files(events_data, output_dir=None):
    """
    Create multiple ICS files from a list of event data.
    
    Args:
        events_data (list): List of event data dictionaries
        output_dir (str): Directory to save the ICS files
            
    Returns:
        list: List of paths to created ICS files
    """
    if not events_data:
        logger.warning("No events provided")
        return []
    
    created_files = []
    
    for event_data in events_data:
        try:
            file_path = create_ics_file(event_data, output_dir)
            created_files.append(file_path)
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            # Continue with other events even if one fails
            continue
    
    return created_files