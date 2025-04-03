"""
Date Extractor and Calendar Generator

This script extracts dates from documents and creates calendar invitation files.

Usage:
    python main.py document.txt
    python main.py document.pdf --output ./calendar_events/
    python main.py document.txt --min-confidence 0.6

Author: AI Assistant
"""

import os
import sys
import argparse
import logging
from datetime import datetime

from document_parser import extract_text_from_file
from date_extractor import extract_dates_from_text, extract_event_metadata
from calendar_generator import create_ics_file
from app import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the date extractor and calendar generator.
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Extract dates from documents and create calendar files"
    )
    parser.add_argument(
        "file", help="Path to the document file"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Output directory for calendar files", 
        default="./calendar_events"
    )
    parser.add_argument(
        "--min-confidence", "-c", 
        help="Minimum confidence level for date extraction (0.0-1.0)", 
        type=float,
        default=0.5
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Extract text from document
        logger.info(f"Extracting text from {args.file}")
        document_text = extract_text_from_file(args.file)
        
        # Extract dates from text
        logger.info("Extracting dates from document")
        date_results = extract_dates_from_text(document_text)
        
        # Filter by confidence
        filtered_dates = [
            (date_str, date_obj, confidence) 
            for date_str, date_obj, confidence in date_results
            if confidence >= args.min_confidence
        ]
        
        if not filtered_dates:
            logger.warning("No dates found with sufficient confidence")
            sys.exit(0)
        
        logger.info(f"Found {len(filtered_dates)} dates with confidence >= {args.min_confidence}")
        
        # Process each date
        events_created = 0
        for date_str, date_obj, confidence in filtered_dates:
            # Find position of date in text
            pos = document_text.find(date_str)
            
            # Extract potential event title and description
            title, description = extract_event_metadata(document_text, pos)
            
            # Create event data
            event_data = {
                'start_time': date_obj,
                'title': title,
                'description': description
            }
            
            # Create ICS file
            logger.info(f"Creating calendar event for date: {date_str} (confidence: {confidence:.2f})")
            ics_file = create_ics_file(event_data, args.output)
            events_created += 1
            
            logger.info(f"Created: {ics_file}")
        
        logger.info(f"Successfully created {events_created} calendar events")
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()