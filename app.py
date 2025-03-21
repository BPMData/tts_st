import streamlit as st
import requests
import base64
import tempfile
import os
import io
from pathlib import Path
import PyPDF2
import docx

# Set page configuration
st.set_page_config(
    page_title="Accessible Text-to-Speech",
    page_icon="🔊",
    layout="wide"
)

# Define voice options
VOICE_OPTIONS = {
    "Bella (f)": "bella",
    "Heart (f)": "heart",
    "Michael (m)": "michael",
    "Alloy (f)": "alloy",
    "Aoede (f)": "aoede",
    "Kore (f)": "kore",
    "Jessica (f)": "jessica",
    "Nicole (f)": "nicole",
    "Nova (f)": "nova",
    "River (f)": "river",
    "Sarah (f)": "sarah",
    "Sky (f)": "sky",
    "Echo (m)": "echo",
    "Eric (m)": "eric",
    "Fenrir (m)": "fenrir",
    "Liam (m)": "liam",
    "Onyx (m)": "onyx",
    "Puck (m)": "puck",
    "Adam (m)": "adam",
    "Santa (m)": "santa"
}

# API key (from Streamlit Secrets)
# For local development, we'll use a fallback if secrets are not available
if "LEMONFOX_API_KEY" in st.secrets:
    LEMONFOX_API_KEY = st.secrets["LEMONFOX_API_KEY"]
else:
    LEMONFOX_API_KEY = "MBqG3Bs0zvWAX9DfaR5wtTSFxyskUDQo"  # Fallback for development

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to convert text to speech using Lemonfox API
def text_to_speech(text, voice):
    url = "https://api.lemonfox.ai/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {LEMONFOX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        return None


# Initialize session state variables
if "text_input" not in st.session_state:
    st.session_state.text_input = ""
if "uploaded_file_text" not in st.session_state:
    st.session_state.uploaded_file_text = ""
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "conversion_complete" not in st.session_state:
    st.session_state.conversion_complete = False
if "input_source" not in st.session_state:
    st.session_state.input_source = "Typed text"

# Main app layout
st.title("Accessible Text-to-Speech")

# Create two columns
col1, col2 = st.columns([3, 2])

with col1:
    st.header("Enter Text")

    # Text input area
    st.session_state.text_input = st.text_area(
        "Type or paste text here",
        height=200,
        value=st.session_state.text_input  # Bind to session state
    )

    st.subheader("Or Upload a File")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a file (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX, TXT"
    )

    # Process uploaded file (only if a new file is uploaded)
    if uploaded_file is not None and uploaded_file.name != st.session_state.get("uploaded_file_name"):
        st.session_state.uploaded_file_name = uploaded_file.name #Store uploaded filename
        file_details = {"Filename": uploaded_file.name, "File size": uploaded_file.size}
        st.write(f"Selected file: {uploaded_file.name}")

        # Extract text based on file type
        try:
            if uploaded_file.name.endswith('.pdf'):
                st.session_state.uploaded_file_text = extract_text_from_pdf(uploaded_file)
                st.success("PDF processed successfully")
            elif uploaded_file.name.endswith('.docx'):
                st.session_state.uploaded_file_text = extract_text_from_docx(uploaded_file)
                st.success("DOCX processed successfully")
            elif uploaded_file.name.endswith('.txt'):
                st.session_state.uploaded_file_text = uploaded_file.getvalue().decode("utf-8")
                st.success("TXT processed successfully")
            # Reset text input if a file is uploaded, and set input source to uploaded file
            st.session_state.text_input = ""
            st.session_state.input_source = "Uploaded file"
            st.session_state.conversion_complete = False #Reset conversion state
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


    # Determine which text to use: uploaded file or text input (using radio buttons)
    if st.session_state.uploaded_file_text and st.session_state.text_input:
        st.session_state.input_source = st.radio("Choose input source", ["Uploaded file", "Typed text"])
        text_to_convert = (
            st.session_state.uploaded_file_text
            if st.session_state.input_source == "Uploaded file"
            else st.session_state.text_input
        )
    elif st.session_state.uploaded_file_text:
        text_to_convert = st.session_state.uploaded_file_text
    else:
        text_to_convert = st.session_state.text_input

    # Voice selection
    st.subheader("Select Voice")
    voice_selection = st.selectbox(
        "Choose a voice",
        options=list(VOICE_OPTIONS.keys()),
        index=0,  # Default to Bella
        format_func=lambda x: x
    )

    # Convert button
    if st.button("Convert to Speech", type="primary"):
        if not text_to_convert:
            st.error("Please enter text or upload a file first.")
        else:
            with st.spinner("Generating speech..."):
                voice_key = VOICE_OPTIONS[voice_selection]
                audio_data = text_to_speech(text_to_convert, voice_key)

                if audio_data:
                    st.session_state.audio_data = audio_data
                    st.session_state.conversion_complete = True
                    st.success("Speech generated successfully!")
                else:
                    st.session_state.conversion_complete = False # Set to false on failure
                    st.session_state.audio_data = None

with col2:
    st.header("Audio Output")

    # Display audio player and download button if conversion is complete
    if st.session_state.conversion_complete and st.session_state.audio_data:
        # Display audio player
        st.audio(st.session_state.audio_data, format="audio/mp3")

        # Display download button
        st.download_button(
            label="Download MP3",
            data=st.session_state.audio_data,
            file_name="speech.mp3",
            mime="audio/mpeg"
        )
    elif st.session_state.conversion_complete and st.session_state.audio_data is None: #Handle API failure case
        st.error("Audio generation failed. Please try again.")
# Footer
st.markdown("---")
st.caption("This application is designed to be fully accessible. If you encounter any issues, please contact your teacher.")
