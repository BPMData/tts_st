# Streamlit Text-to-Speech Application

This is a fully accessible text-to-speech web application built with Streamlit that uses the Lemonfox.ai API for high-quality speech synthesis.

## Features

- Clean, minimalist design with responsive layout
- Full accessibility support with proper ARIA attributes
- Text input for any length of text
- File upload capability for PDF, DOCX, and TXT files
- 20 different natural-sounding voices (default: Bella)
- Audio playback in the browser
- MP3 download option

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.streamlit/secrets.toml` file with your Lemonfox API key:
   ```
   LEMONFOX_API_KEY = "your_api_key_here"
   ```

## Usage

Run the application with:
```
streamlit run app.py
```

## Deployment

This application can be deployed to Streamlit Cloud or any other platform that supports Streamlit applications.

## Credits

Created by a high school computer science teacher to help students with vision impairments.
