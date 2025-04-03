"""
Test script to verify the syllabus assessment extraction.
This uses the specialized syllabus_extractor module to extract assessments from course syllabi.
"""

import os
import json
from document_parser import parse_document
from syllabus_extractor import get_assessments_json

def test_syllabus(file_path):
    """
    Test the assessment extraction on a single syllabus file.
    
    Args:
        file_path (str): Path to the syllabus PDF file
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
    
    # Parse the document to extract text
    try:
        print(f"\n===== Testing {os.path.basename(file_path)} =====")
        text = parse_document(file_path)
        print(f"Successfully parsed document.")
        print(f"Extracted {len(text)} characters of text")
        
        # Extract structured events using the specialized syllabus extractor
        assessments_json = get_assessments_json(text)
        assessments = json.loads(assessments_json)
        
        print("\nExtracted Assessments:")
        print(json.dumps(assessments, indent=2))
        print(f"\nFound {len(assessments)} assessments")
        return len(assessments)
        
    except Exception as e:
        print(f"Error processing document: {e}")
        return 0

def main():
    # Define syllabus files to test
    syllabus_files = [
        "./attached_assets/W25 ENTI 674 L01-L02 - Course Outline - Mohammad Keyhani1.pdf",
        "./attached_assets/W25 FNCE 674 L01-L02 Q4 Course Outline - Peggy Hedges.pdf",
        "./attached_assets/W25 OBHR 674 L01-L02 Course Outline Audrey Farrier.pdf",
        "./attached_assets/W25 SGMA 672 L01-L02 Q4 Course Outline Astrid Eckstein.pdf"
    ]
    
    total_assessments = 0
    
    # Test each syllabus file
    for file_path in syllabus_files:
        count = test_syllabus(file_path)
        total_assessments += count
    
    print("\n===== Summary =====")
    print(f"Total assessments found across all syllabi: {total_assessments}")
    print("Note: Look for weekly assignments and participation events which should be added now.")

if __name__ == "__main__":
    main()