"""
Test script to demonstrate extraction of assessments from syllabi 
and generation of calendar events.

This script:
1. Processes multiple syllabi
2. Extracts assessment deadlines from each one
3. Generates an ICS file for each assessment
4. Summarizes the results
"""

import json
import os
from datetime import datetime
from document_parser import parse_document
from syllabus_extractor import extract_assessments_from_syllabus
from calendar_generator import create_multiple_ics_files


def main():
    # Ensure output directory exists
    output_dir = './calendar_events'
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear any existing files to avoid confusion
    for file in os.listdir(output_dir):
        if file.endswith('.ics'):
            os.remove(os.path.join(output_dir, file))
    
    # Test each syllabus
    syllabi = [
        'attached_assets/W25 ENTI 674 L01-L02 - Course Outline - Mohammad Keyhani1.pdf',
        'attached_assets/W25 FNCE 674 L01-L02 Q4 Course Outline - Peggy Hedges.pdf',
        'attached_assets/W25 OBHR 674 L01-L02 Course Outline Audrey Farrier.pdf',
        'attached_assets/W25 SGMA 672 L01-L02 Q4 Course Outline Astrid Eckstein.pdf'
    ]
    
    all_assessments = []
    all_events = []
    
    print("= Syllabus Assessment Extractor and Calendar Generator =\n")
    
    for syllabus_path in syllabi:
        # Display the course name
        course_name = os.path.basename(syllabus_path).split(' ', 2)[1]
        print(f"\nProcessing {course_name} syllabus...")
        
        # Parse the document
        text = parse_document(syllabus_path)
        print(f"  - Extracted {len(text)} characters")
        
        # Extract assessments
        assessments = extract_assessments_from_syllabus(text)
        print(f"  - Found {len(assessments)} assessments")
        
        for assessment in assessments:
            # Convert to event format for calendar generator
            # Handle various time formats used in assessments
            time_str = assessment.get("time", "").lower()
            
            # Start with just the date at midnight
            if assessment["date"]:
                try:
                    start_time = datetime.strptime(assessment["date"], "%Y-%m-%d")
                except ValueError:
                    # Skip assessments with invalid dates
                    print(f"    - Warning: Skipping assessment with invalid date: {assessment['title']}")
                    continue
            else:
                # Skip assessments without dates
                print(f"    - Warning: Skipping assessment without date: {assessment['title']}")
                continue
                
            # Set end time based on time description
            if "during class" in time_str or "in class" in time_str:
                # Assume class is 3 hours
                end_time = datetime(start_time.year, start_time.month, start_time.day, 
                                   start_time.hour + 3, start_time.minute)
            else:
                # Default to all-day event (same end time)
                end_time = start_time
            
            # Format title with course name
            course_code = course_name.split(' ')[0]
            title = f"{course_code}: {assessment['title']}"
            
            event = {
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "description": f"Course: {course_name}\nAssessment: {assessment['title']}\nTime: {assessment['time']}"
            }
            
            all_events.append(event)
            print(f"    - Added: {title} on {assessment['date']}")
        
        all_assessments.extend(assessments)
    
    # Generate calendar files
    print("\nGenerating calendar files...")
    ics_files = create_multiple_ics_files(all_events, output_dir)
    
    print(f"\nSuccess! Generated {len(ics_files)} calendar files in {output_dir}/")
    for i, file_path in enumerate(ics_files):
        print(f"  {i+1}. {os.path.basename(file_path)}")
    
    print("\nSummary of all extracted assessments:")
    print(json.dumps(all_assessments, indent=2))


if __name__ == "__main__":
    main()