"""
Syllabus Assessment Extractor

A specialized module for extracting assessments from course syllabi in structured format.
This module specifically targets academic assessment deadlines and formats them in a consistent JSON structure.
"""

import re
import json
from datetime import datetime, timedelta

def handle_weekly_assignments(text, events):
    """
    Check for weekly assignments and participation and add recurring events.
    
    Args:
        text (str): The syllabus text content
        events (list): Existing events list
        
    Returns:
        list: Updated events list with weekly assignments included
    """
    # Check if there are any mentions of weekly assignments or readings
    weekly_patterns = [
        r'(?:assignment|reading|quiz).*?(?:weekly|each week|following each week|due weekly)',
        r'(?:weekly|each week|following each week).*?(?:assignment|reading|quiz)',
        r'(?:due|submit).*?(?:following|after).*?(?:class|lecture|session)',
        r'(?:weekly).*?(?:assignment|deliverable|submission)'
    ]
    
    # If we find any pattern suggesting weekly assignments
    for pattern in weekly_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Find what type of weekly assignment it is
            assignment_type = "Weekly Assignment"
            
            if 'reading' in text.lower():
                assignment_type = "Weekly Reading"
            elif 'quiz' in text.lower():
                assignment_type = "Weekly Quiz"
            elif 'discussion' in text.lower():
                assignment_type = "Weekly Discussion"
            elif 'report' in text.lower():
                assignment_type = "Weekly Report"
            
            # Find the start and end dates by looking at existing events
            if events:
                # Sort existing events by date
                sorted_events = sorted(events, key=lambda x: x["date"])
                
                # Get the earliest and latest dates
                start_date = sorted_events[0]["date"]
                end_date = sorted_events[-1]["date"]
                
                # Convert to datetime objects
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                # Create weekly events (one week apart)
                current_dt = start_dt
                while current_dt <= end_dt:
                    # Only add if not already on the same day as another event
                    current_date = current_dt.strftime('%Y-%m-%d')
                    
                    # Check if this day already has an event
                    day_has_event = False
                    for event in events:
                        if event["date"] == current_date:
                            day_has_event = True
                            break
                    
                    # If no event on this day, add weekly assignment
                    if not day_has_event:
                        events.append({
                            "title": assignment_type,
                            "date": current_date,
                            "time": "weekly"
                        })
                    
                    # Move to next week
                    current_dt = datetime(
                        current_dt.year, 
                        current_dt.month, 
                        current_dt.day + 7
                    )
            
            # No need to check other patterns if we found one
            break
    
    return events


def add_participation_events(text, events):
    """
    Add participation events if mentioned in the syllabus.
    
    Args:
        text (str): The syllabus text content
        events (list): Existing events list
        
    Returns:
        list: Updated events list with participation events included
    """
    # Check if there are mentions of participation
    participation_patterns = [
        r'(?:participation|attendance).*?(?:on-going|ongoing|weekly|throughout)',
        r'(?:on-going|ongoing|weekly|throughout).*?(?:participation|attendance)',
        r'(?:participation).*?(?:\d{1,2}%|\d{1,2}\s*percent)'
    ]
    
    # If we find any pattern suggesting participation is graded
    for pattern in participation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Find the start and end dates by looking at existing events
            if events:
                # Sort existing events by date
                sorted_events = sorted(events, key=lambda x: x["date"])
                
                # Get the earliest and latest dates
                start_date = sorted_events[0]["date"]
                end_date = sorted_events[-1]["date"]
                
                # Convert to datetime objects
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                # Create weekly participation events (one week apart)
                current_dt = start_dt
                while current_dt <= end_dt:
                    # Only add if not already on the same day as another event
                    current_date = current_dt.strftime('%Y-%m-%d')
                    
                    # Check if this day already has a participation event
                    has_participation = False
                    for event in events:
                        if event["date"] == current_date and "participation" in event["title"].lower():
                            has_participation = True
                            break
                    
                    # If no participation event on this day, add it
                    if not has_participation:
                        events.append({
                            "title": "Class Participation",
                            "date": current_date,
                            "time": "throughout the course"
                        })
                    
                    # Move to next week
                    current_dt = datetime(
                        current_dt.year, 
                        current_dt.month, 
                        current_dt.day + 7
                    )
            
            # No need to check other patterns if we found one
            break
    
    return events


def extract_assessments_from_syllabus(text):
    """
    Extract assessments from a syllabus and return structured data.
    
    Args:
        text (str): The syllabus text content
        
    Returns:
        list: List of assessment dictionaries with title, date, and time
    """
    events = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Step 1: Look for pattern that indicates this is a course syllabus
    course_code_match = re.search(r'(ENTI|FNCE|OBHR|SGMA|MKTG|ACCT)\s*\d{3}', text)
    if not course_code_match:
        # Not a course syllabus, return empty list
        return []
    
    course_code = course_code_match.group(1)
    
    # Step 2: Handle different course syllabi formats
    if "ENTI" in course_code:
        # ENTI pattern: extract midterm, project, lab
        events.extend(extract_enti_assessments(text))
    elif "FNCE" in course_code:
        # FNCE pattern: extract case write-ups, quizzes, in-class exercises
        events.extend(extract_fnce_assessments(text))
    elif "OBHR" in course_code:
        # OBHR pattern: extract assessments from OBHR syllabi 
        events.extend(extract_obhr_assessments(text))
    elif "SGMA" in course_code:
        # SGMA pattern: extract exams, papers
        events.extend(extract_sgma_assessments(text))
    else:
        # General extraction for any course syllabus
        events.extend(extract_general_course_assessments(text))
    
    # If no events found with specific extractors, try the general method
    if not events:
