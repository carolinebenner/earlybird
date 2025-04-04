"""
Debug script for syllabus extraction.
"""

import sys
import traceback
import json
from document_parser import parse_pdf_file
from syllabus_extractor import extract_assessments_from_syllabus

def debug_extraction(file_path):
    """Debug the extraction process for a syllabus file."""
    try:
        print(f"Processing {file_path}...")
        
        # Parse the file
        text = parse_pdf_file(file_path)
        print(f"Successfully parsed document. Extracted {len(text)} characters.")
        
        # Extract assessments
        assessments = extract_assessments_from_syllabus(text)
        print("Successfully extracted assessments:")
        print(json.dumps(assessments, indent=2))
        
        print(f"Found {len(assessments)} assessments")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_extractor.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = debug_extraction(file_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()