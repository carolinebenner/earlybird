# Early Bird - Syllabus Date Extraction Tool

Early Bird is a sophisticated syllabus processing platform that automatically extracts, analyzes, and transforms academic document information into actionable insights and calendar events.

## Features

- **Multi-format Document Parsing**: Process text, PDF, and Word documents
- **Intelligent Date Extraction**: Identify and extract assessment deadlines from syllabi
- **Calendar Integration**: Generate ICS files or directly add events to Google/Microsoft calendars
- **User-friendly Interface**: Modern responsive design with light/dark mode options
- **Preview & Edit**: Review extracted dates before calendar generation

## Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Document Processing**: PyPDF2, python-docx
- **Date Parsing**: python-dateutil
- **Calendar Generation**: icalendar
- **Authentication**: Google OAuth, Microsoft OAuth
- **Database**: SQLAlchemy with PostgreSQL

## Setup & Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database

### Environment Variables

- DATABASE_URL: PostgreSQL connection string
- GOOGLE_OAUTH_CLIENT_ID & GOOGLE_OAUTH_CLIENT_SECRET: For Google Calendar integration
- MICROSOFT_OAUTH_CLIENT_ID & MICROSOFT_OAUTH_CLIENT_SECRET: For Microsoft Outlook integration

### Installation

1. Clone the repository
2. Install dependencies from requirements.txt
3. Configure the environment variables
4. Run the application with "python main.py"

## Usage

### Web Interface

1. Navigate to the application in your web browser: https://date-extract-calendar-carolineobenner.replit.app/
2. Upload a syllabus document (PDF, DOCX, or TXT)
3. Review the extracted assessment deadlines
4. Generate calendar files or add events directly to your calendar

## Team

This project was created by Master of Management students at the Haskayne School of Business, University of Calgary, as a final project for ENTI 674.
