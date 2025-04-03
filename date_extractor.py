"""
Date Extractor Module

This module contains functions for extracting dates from text using various methods.
"""

import re
import logging
from datetime import datetime, timedelta
from dateutil import parser, tz

logger = logging.getLogger(__name__)

# Regex patterns for date extraction
DATE_PATTERNS = [
    # Common date formats (MM/DD/YYYY, DD/MM/YYYY, YYYY/MM/DD)
    r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b',
    
    # Written dates (January 1, 2025; 1st of January, 2025)
    r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),?\s+\d{4}\b',
    
    # ISO dates (YYYY-MM-DD)
    r'\b\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}\b',
    
    # Named days with dates (Monday, January 1)
    r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b',
    
    # Relative dates (next Monday, this Friday)
    r'\b(?:this|next|last|coming|upcoming)\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
    
    # Month and year only (January 2025)
    r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b',
    
    # Day and month only (January 1)
    r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b',
]

# Patterns for time extraction
TIME_PATTERNS = [
    # 12-hour format (1:30 PM, 1:30 pm, 1:30PM, 1:30pm)
    r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|a\.m\.|p\.m\.)\b',
    r'\b\d{1,2}\s*(?:AM|PM|am|pm|a\.m\.|p\.m\.)\b',
    
    # 24-hour format (13:30, 13:30:00)
    r'\b\d{1,2}:\d{2}(?::\d{2})?\b',
    
    # Written times (1 o'clock, half past 2)
    r'\b\d{1,2}\s+o\'clock\b',
    r'\bhalf\s+past\s+\d{1,2}\b',
    r'\bquarter\s+(?:past|to)\s+\d{1,2}\b',
]

# Common date-related words to help with context extraction
DATE_CONTEXT_WORDS = [
    "meeting", "appointment", "schedule", "event", "conference", "session",
    "deadline", "due", "by", "until", "seminar", "workshop", "class",
    "lecture", "presentation", "call", "interview", "discussion"
]


def extract_dates_from_text(text):
    """
    Extract potential date strings from text.
    
    Args:
        text (str): The text to extract dates from
        
    Returns:
        list: A list of tuples containing (date_string, parsed_date, confidence)
    """
    results = []
    date_positions = []
    
    # Try to extract dates using regex patterns
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text):
            date_str = match.group()
            pos = match.start()
            
            # Extract surrounding context
            context = get_surrounding_text(text, pos, 200)
            
            # Try to extract time from context
            time_str = extract_time_from_text(context)
            
            try:
                # Try to parse the date
                parsed_date = parser.parse(date_str, fuzzy=True)
                
                # If we found a time in the context, update the date with it
                if time_str:
                    try:
                        time_obj = parser.parse(time_str)
                        parsed_date = parsed_date.replace(
                            hour=time_obj.hour,
                            minute=time_obj.minute,
                            second=time_obj.second
                        )
                    except:
                        # If time parsing fails, just keep the original date
                        pass
                
                # Set current year if the parser defaulted to 1900
                current_year = datetime.now().year
                if parsed_date.year < 2000:
                    parsed_date = parsed_date.replace(year=current_year)
                
                # Calculate confidence level
                confidence = calculate_confidence(date_str, parsed_date)
                
                # Add to results if not already found (avoid duplicates)
                if pos not in date_positions:
                    results.append((date_str, parsed_date, confidence))
                    date_positions.append(pos)
            
            except (ValueError, OverflowError) as e:
                # Skip invalid dates
                logger.debug(f"Failed to parse date '{date_str}': {e}")
                continue
    
    return results


def extract_time_from_text(text):
    """
    Extract time information from text.
    
    Args:
        text (str): The text to extract time from
        
    Returns:
        str: Extracted time string or None
    """
    for pattern in TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group()
    
    return None


def get_surrounding_text(text, position, window_size):
    """
    Get surrounding text around a position with a specific window size.
    
    Args:
        text (str): The original text
        position (int): The position to center around
        window_size (int): The window size in characters
        
    Returns:
        str: Text around the position
    """
    start = max(0, position - window_size // 2)
    end = min(len(text), position + window_size // 2)
    
    return text[start:end]


def calculate_confidence(date_str, parsed_date):
    """
    Calculate confidence level for an extracted date.
    
    Args:
        date_str (str): The original date string
        parsed_date (datetime): The parsed date object
        
    Returns:
        float: Confidence level between 0 and 1
    """
    confidence = 0.5  # Start with a medium confidence
    
    # Future dates get higher confidence
    now = datetime.now()
    if parsed_date > now:
        confidence += 0.1
    
    # If the date is too far in the future, reduce confidence
    if parsed_date > now + timedelta(days=365):
        confidence -= 0.2
    
    # If the date includes year, increase confidence
    if re.search(r'\b\d{4}\b', date_str):
        confidence += 0.1
    
    # If the date includes both day and month, increase confidence
    if re.search(r'\b\d{1,2}[/\-\.]\d{1,2}\b', date_str) or \
       re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b', date_str):
        confidence += 0.1
    
    # If the date includes a weekday, increase confidence
    if re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', date_str, re.IGNORECASE):
        confidence += 0.1
    
    # Cap the confidence between 0 and 1
    return max(0.1, min(0.95, confidence))


def extract_event_metadata(text, date_pos):
    """
    Extract potential event title and description from text around a date.
    
    Args:
        text (str): The full document text
        date_pos (int): Position of the date in text
        
    Returns:
        tuple: (title, description)
    """
    # Extract a larger context around the date
    context = get_surrounding_text(text, date_pos, 400)
    
    # Try to find sentence boundaries
    sentences = re.split(r'[.!?]\s+', context)
    
    # Find the sentence containing the date
    date_sentence = ""
    for sentence in sentences:
        relative_pos = context.find(sentence)
        if relative_pos <= len(context) // 2 <= relative_pos + len(sentence):
            date_sentence = sentence
            break
    
    # If we couldn't find a sentence, use a 100-char window
    if not date_sentence:
        date_sentence = get_surrounding_text(context, len(context) // 2, 100)
    
    # Look for context words that might indicate an event
    title = None
    for word in DATE_CONTEXT_WORDS:
        if word in date_sentence.lower():
            # Find the nearest phrase containing this context word
            pattern = r'([^.!?]*\b' + re.escape(word) + r'\b[^.!?]*)'
            match = re.search(pattern, date_sentence, re.IGNORECASE)
            if match:
                title_candidate = match.group(1).strip()
                # Use the first 50 chars max as a title
                title = title_candidate[:50].strip()
                if len(title_candidate) > 50:
                    title += "..."
                break
    
    # If no title was found, look for capitalized phrases
    if not title:
        # Find phrases with capitalized words (potential titles)
        cap_phrases = re.findall(r'([A-Z][^.!?:]*(?:[:.]\s*|$))', date_sentence)
        if cap_phrases:
            # Use the longest capitalized phrase
            title = max(cap_phrases, key=len).strip()
            # Limit length
            if len(title) > 50:
                title = title[:50].strip() + "..."
    
    # If still no title, use the date sentence itself
    if not title:
        # Truncate the date sentence if too long
        if len(date_sentence) > 50:
            title = date_sentence[:50].strip() + "..."
        else:
            title = date_sentence.strip()
    
    # Description is the full context
    description = context.strip()
    
    return title, description