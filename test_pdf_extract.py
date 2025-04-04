"""
Test script to extract and print text from a PDF file.
"""

import sys
from document_parser import parse_pdf_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extract.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        text = parse_pdf_file(file_path)
        print(f"Successfully extracted {len(text)} characters of text.")
        print("\nFirst 1000 characters:")
        print("-" * 50)
        print(text[:1000])
        print("-" * 50)
        
        print("\nSearching for assessment sections...")
        assessment_keywords = ["assessment", "assignments", "deliverables", "evaluation", "grading", "course requirements"]
        for keyword in assessment_keywords:
            position = text.lower().find(keyword)
            if position != -1:
                start = max(0, position - 50)
                end = min(len(text), position + 400)
                print(f"\nFound '{keyword}' at position {position}:")
                print(text[start:end])
        
        print("\nLooking for specific exercise types...")
        exercise_keywords = ["exercise", "project", "presentation", "paper", "report", "case", "quiz", "exam"]
        for keyword in exercise_keywords:
            # Find all occurrences
            text_lower = text.lower()
            start_pos = 0
            found_count = 0
            
            while found_count < 3:  # Limit to 3 occurrences per keyword
                position = text_lower.find(keyword, start_pos)
                if position == -1:
                    break  # No more occurrences
                
                start = max(0, position - 100)
                end = min(len(text), position + 300)
                print(f"\nFound '{keyword}' at position {position}:")
                print(text[start:end])
                
                start_pos = position + len(keyword)  # Move past this occurrence
                found_count += 1
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()