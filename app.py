import streamlit as st
import requests
import base64
import PyPDF2
import docx
from image_backend import look_at_photo, encode_image_from_bytes  # Import both


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
if "LEMONFOX_API_KEY" in st.secrets:
    LEMONFOX_API_KEY = st.secrets["LEMONFOX_API_KEY"]

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
if "image_description" not in st.session_state:
    st.session_state.image_description = ""
if "captured_image" not in st.session_state:
    st.session_state.captured_image = None  # Initialize to None
if 'camera_key' not in st.session_state:
    st.session_state.camera_key = "camera_1"
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None  # Initialize to None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None


# --- Main App Layout ---
st.title("Accessible Text-to-Speech")
col1, col2 = st.columns([3, 2])

with col1:
    st.header("Enter Text")

    # Text input area
    st.session_state.text_input = st.text_area(
        "Type or paste text here",
        height=200,
        value=st.session_state.text_input
    )

    st.subheader("Or Upload a File")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a file (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX, TXT"
    )

    # Process uploaded file
    if uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_file_name:
        st.session_state.uploaded_file_name = uploaded_file.name
        st.write(f"Selected file: {uploaded_file.name}")
        try:
            if uploaded_file.name.endswith('.pdf'):
                st.session_state.uploaded_file_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                st.session_state.uploaded_file_text = extract_text_from_docx(uploaded_file)
            elif uploaded_file.name.endswith('.txt'):
                st.session_state.uploaded_file_text = uploaded_file.getvalue().decode("utf-8")
            st.success(f"{uploaded_file.name.split('.')[-1].upper()} processed successfully")
            st.session_state.text_input = ""
            st.session_state.image_description = ""  # Clear any previous image description
            st.session_state.input_source = "Uploaded file"
            st.session_state.conversion_complete = False
            # Clear image states
            st.session_state.captured_image = None
            st.session_state.uploaded_image = None

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

    # Determine text to convert
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
        index=0,
        format_func=lambda x: x
    )

    # Convert button
    if st.button("Convert to Speech", type="primary"):
        if not text_to_convert:
            st.error("Please enter text, upload a file, or use an image.")
        else:
            with st.spinner("Generating speech..."):
                voice_key = VOICE_OPTIONS[voice_selection]
                audio_data = text_to_speech(text_to_convert, voice_key)
                if audio_data:
                    st.session_state.audio_data = audio_data
                    st.session_state.conversion_complete = True
                    st.success("Speech generated successfully!")
                else:
                    st.session_state.conversion_complete = False
                    st.session_state.audio_data = None

with col2:
    st.header("Audio Output")

    if st.session_state.conversion_complete and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format="audio/mp3")
        st.download_button(
            label="Download MP3",
            data=st.session_state.audio_data,
            file_name="speech.mp3",
            mime="audio/mpeg"
        )
    elif st.session_state.conversion_complete and st.session_state.audio_data is None:
        st.error("Audio generation failed. Please try again.")

    # --- Image Handling in col2 (Separate Expanders) ---
    with st.expander("Capture Photo"):
        captured_image = st.camera_input("Take a picture", key=st.session_state.camera_key)
        if captured_image and captured_image != st.session_state.captured_image:
            st.session_state.captured_image = captured_image
            st.session_state.uploaded_image = None  # Clear uploaded image
            st.image(captured_image)  # Display immediately
            bytes_data = captured_image.getvalue()
            base64_image = encode_image_from_bytes(bytes_data)
            with st.spinner("Analyzing photo..."):
                st.session_state.image_description = look_at_photo(base64_image, upload=False)
                st.session_state.text_input = st.session_state.image_description
                st.session_state.uploaded_file_text = ""  # Clear any file text
                st.session_state.input_source = "Typed text"
                st.rerun()


    with st.expander("Upload Image"):
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_image and uploaded_image != st.session_state.uploaded_image:
            st.session_state.uploaded_image = uploaded_image
            st.session_state.captured_image = None  # Clear captured image
            st.session_state.camera_key = "camera_2" if st.session_state.camera_key == "camera_1" else "camera_1"
            st.image(uploaded_image)  # Display immediately
            bytes_data = uploaded_image.getvalue()
            base64_image = encode_image_from_bytes(bytes_data)
            with st.spinner("Analyzing image..."):
                st.session_state.image_description = look_at_photo(base64_image, upload=True)
                st.session_state.text_input = st.session_state.image_description
                st.session_state.uploaded_file_text = ""  # Clear any file text
                st.session_state.input_source = "Typed text"
                st.rerun()

# Footer
st.markdown("---")
st.caption("This application is designed to be fully accessible. If you encounter any issues, please contact your teacher.")
