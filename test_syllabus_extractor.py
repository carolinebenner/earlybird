"""
Test script to verify the syllabus assessment extraction.
This uses the specialized syllabus_extractor module to extract assessments from course syllabi.
"""

import os
import json
from document_parser import parse_document
from syllabus_extractor import get_assessments_json

def main():
    # Path to the sample syllabus PDF
    pdf_path = "attached_assets/W25 ENTI 674 L01-L02 - Course Outline - Mohammad Keyhani1.pdf"
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return
    
    # Parse the document to extract text
    try:
        text = parse_document(pdf_path)
        print(f"Successfully parsed {pdf_path}")
        print(f"Extracted {len(text)} characters of text")
        
        # Extract structured events using the specialized syllabus extractor
        assessments_json = get_assessments_json(text)
        assessments = json.loads(assessments_json)
        
        print("\nExtracted Assessments:")
        print(json.dumps(assessments, indent=2))
        print(f"\nFound {len(assessments)} assessments")
        
    except Exception as e:
        print(f"Error processing document: {e}")

if __name__ == "__main__":
    main()