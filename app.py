# --- Start of Updated Code ---

import streamlit as st
import requests
import base64
import PyPDF2
import docx
import io

# Import functions from image_backend.py (assuming it's in the same directory)
try:
    from image_backend import look_at_photo, encode_image_from_bytes
except ImportError:
    st.error("🚨 FATAL ERROR: image_backend.py not found. Image analysis features will fail.")
    # Define dummy functions to prevent NameErrors, but show error
    def encode_image_from_bytes(byte_data): return base64.b64encode(byte_data).decode('utf-8')
    def look_at_photo(base64_image, upload=False): return "Error: image_backend.py not loaded."


# --- Configuration ---
st.set_page_config(
    page_title="Accessible Text-to-Speech",
    page_icon="🔊",
    layout="wide"
)

# --- Constants ---
VOICE_OPTIONS = {
    "Bella (f)": "bella", "Heart (f)": "heart", "Michael (m)": "michael",
    "Alloy (f)": "alloy", "Aoede (f)": "aoede", "Kore (f)": "kore",
    "Jessica (f)": "jessica", "Nicole (f)": "nicole", "Nova (f)": "nova",
    "River (f)": "river", "Sarah (f)": "sarah", "Sky (f)": "sky",
    "Echo (m)": "echo", "Eric (m)": "eric", "Fenrir (m)": "fenrir",
    "Liam (m)": "liam", "Onyx (m)": "onyx", "Puck (m)": "puck",
    "Adam (m)": "adam", "Santa (m)": "santa"
}
LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
TTS_MODEL = "tts-1"
MAX_CHAR_LIMIT = 10000 # Character limit for TTS input
DEFAULT_SOURCE_INFO = "Enter text, upload a file, or use an image."

# --- API Keys Check ---
# IMPORTANT: Requires both OPENAI_API_KEY (for image analysis) and
# LEMONFOX_API_KEY (for text-to-speech) in Streamlit Secrets ([secrets].toml)

missing_keys = []
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

if not OPENAI_API_KEY:
    missing_keys.append("OPENAI_API_KEY (for image analysis)")
if not LEMONFOX_API_KEY:
    missing_keys.append("LEMONFOX_API_KEY (for text-to-speech)")

if missing_keys:
    keys_str = " and ".join(missing_keys)
    st.error(f"🚨 Error: API Key(s) not found in Streamlit Secrets: {keys_str}. Related features will be disabled.")
    # Optionally disable buttons or st.stop()

# --- Helper Functions (extract_text_from_pdf, extract_text_from_docx - unchanged) ---
def extract_text_from_pdf(file_bytes_io):
    """Extracts text from a PDF file provided as BytesIO."""
    try:
        pdf_reader = PyPDF2.PdfReader(file_bytes_io)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text
    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF: This might be due to an encrypted or corrupted file. ({e})")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during PDF processing: {e}")
        return None

def extract_text_from_docx(file_bytes_io):
    """Extracts text from a DOCX file provided as BytesIO."""
    try:
        doc = docx.Document(file_bytes_io)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e: # Consider adding specific docx exceptions if needed
        st.error(f"Error reading DOCX file: {e}")
        return None

# --- Helper Function: text_to_speech (modified slightly for clarity) ---
def text_to_speech(text, voice_key):
    """Converts text to speech using the Lemonfox API."""
    if not LEMONFOX_API_KEY: # Use the globally checked key
        st.error("Cannot convert to speech: Lemonfox API Key is missing.")
        return None
    if not text:
        st.warning("Cannot convert empty text to speech.")
        return None

    if len(text) > MAX_CHAR_LIMIT:
        st.error(f"Error: Text length ({len(text)} characters) exceeds the TTS limit of {MAX_CHAR_LIMIT}. Please shorten or chunk the text.")
        return None

    headers = {
        "Authorization": f"Bearer {LEMONFOX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": TTS_MODEL,
        "input": text,
        "voice": voice_key,
        "response_format": "mp3"
    }

    try:
        with st.spinner("🔊 Generating speech via Lemonfox API..."):
            response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
            response.raise_for_status()
        st.success("✅ Speech generated successfully!")
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Lemonfox API Request Error: Failed to connect or communicate. ({e})")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during TTS conversion: {e}")
        return None

# --- Helper Function: process_and_speak_image (WITH DEBUGGING) ---
def process_and_speak_image(image_bytes, voice_key, is_upload):
    """Analyzes image using OpenAI, checks length, converts description to Lemonfox speech."""
    st.write("--- DEBUG: Entered process_and_speak_image ---") # DEBUG
    description = None

    # --- Step 1: Analyze Image ---
    if not OPENAI_API_KEY:
         st.error("Cannot analyze image: OpenAI API Key is missing.")
         st.write("--- DEBUG: OpenAI Key MISSING ---") # DEBUG
         return

    try:
        st.write(f"--- DEBUG: Preparing to analyze image (upload={is_upload}). Bytes length: {len(image_bytes)} ---") # DEBUG
        with st.spinner("🖼️ Analyzing image via OpenAI API..."):
            base64_image = encode_image_from_bytes(image_bytes)
            st.write("--- DEBUG: Base64 encoding complete. Calling look_at_photo... ---") # DEBUG
            # Assuming look_at_photo uses st.secrets['OPENAI_API_KEY'] internally
            description = look_at_photo(base64_image, upload=is_upload)
            st.write(f"--- DEBUG: look_at_photo returned: {description} ---") # DEBUG

        # Check if analysis returned a valid description string
        if not description or "error" in description.lower() or "fail" in description.lower():
             st.error(f"Image analysis failed or returned an error: {description}")
             st.write(f"--- DEBUG: Analysis FAILED or returned error description: '{description}' ---") # DEBUG
             description = None # Ensure description is None if analysis failed

    except Exception as e:
        st.error(f"Error during image analysis call: {e}")
        st.write(f"--- DEBUG: EXCEPTION during analysis: {e} ---") # DEBUG
        description = None

    # --- Step 2: Update State and Convert to Speech (if analysis succeeded) ---
    if description:
        st.write("--- DEBUG: Analysis SUCCESSFUL. Preparing to update state and call TTS. ---") # DEBUG
        st.session_state.image_description = description
        st.session_state.text_input = description # Update text area state value
        st.session_state.uploaded_file_text = ""
        st.session_state.active_source_info = "Using text from analyzed image"
        st.session_state.conversion_complete = False
        st.write(f"--- DEBUG: Set st.session_state.text_input to: '{st.session_state.text_input}' ---") # DEBUG

        # --- Step 3: Convert Description to Speech ---
        st.write("--- DEBUG: Calling text_to_speech... ---") # DEBUG
        audio_data = text_to_speech(description, voice_key)
        if audio_data:
            st.write("--- DEBUG: text_to_speech returned audio data. ---") # DEBUG
            st.session_state.audio_data = audio_data
            st.session_state.conversion_complete = True
        else:
            st.write("--- DEBUG: text_to_speech returned NO audio data (failed). ---") # DEBUG
            st.session_state.audio_data = None
            st.session_state.conversion_complete = False
    else:
        # If analysis failed or returned None/error string
        st.write("--- DEBUG: Skipping state update and TTS because description is invalid/None. ---") # DEBUG
        st.warning("Could not generate speech because image analysis failed.")
        # Let's NOT clear text_input here if analysis failed, maybe previous text is useful?
        # st.session_state.text_input = "" # Reconsider clearing this
        st.session_state.image_description = ""
        # Only reset source info if there isn't already text typed manually
        if not st.session_state.text_input and not st.session_state.uploaded_file_text:
             st.session_state.active_source_info = DEFAULT_SOURCE_INFO

    st.write("--- DEBUG: Exiting process_and_speak_image ---") # DEBUG

# --- Initialize Session State (Unchanged) ---
default_values = {
    "text_input": "", "uploaded_file_text": "", "uploaded_file_name": None,
    "image_description": "", "audio_data": None, "conversion_complete": False,
    "active_source_info": DEFAULT_SOURCE_INFO, "captured_image": None,
    "uploaded_image": None, "camera_key": "camera_1", "uploader_key": "uploader_1",
    "processed_file_name": None # Added to track processed file
}
for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Main App Layout ---
st.title("Accessible Text-to-Speech 🔊")

col1, col2 = st.columns([3, 2])

# --- Column 1: Text Input and File Upload ---
with col1:
    st.header("1. Provide Text")
    st.info(f"**Source:** {st.session_state.active_source_info}")

    # Text input area
    user_typed_text = st.text_area(
        "Type or paste text here", height=200, value=st.session_state.text_input,
        key="text_area_input", help=f"Max {MAX_CHAR_LIMIT} chars for TTS."
    )
    if user_typed_text != st.session_state.text_input:
         st.session_state.text_input = user_typed_text
         if user_typed_text:
             st.session_state.active_source_info = "Using typed text"
             st.session_state.uploaded_file_text = ""
             st.session_state.uploaded_file_name = None
             st.session_state.image_description = ""
             st.session_state.conversion_complete = False
             st.session_state.audio_data = None
         elif not st.session_state.uploaded_file_text and not st.session_state.image_description:
             st.session_state.active_source_info = DEFAULT_SOURCE_INFO

    st.subheader("Or Upload a File")
    uploaded_file = st.file_uploader(
        "Upload (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"],
        help=f"Max text length: {MAX_CHAR_LIMIT} characters.",
        key=st.session_state.uploader_key
    )

    # Process uploaded file (Logic largely unchanged, includes length check)
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.get('processed_file_name', None):
            st.session_state.processed_file_name = uploaded_file.name
            st.write(f"Processing file: `{uploaded_file.name}`")
            file_text = None
            try:
                bytes_data = io.BytesIO(uploaded_file.getvalue())
                # ... (PDF, DOCX, TXT extraction logic remains the same) ...
                if uploaded_file.name.lower().endswith('.pdf'):
                    file_text = extract_text_from_pdf(bytes_data)
                elif uploaded_file.name.lower().endswith('.docx'):
                    file_text = extract_text_from_docx(bytes_data)
                elif uploaded_file.name.lower().endswith('.txt'):
                    try:
                        file_text = bytes_data.getvalue().decode("utf-8")
                    except UnicodeDecodeError:
                         try:
                             file_text = bytes_data.getvalue().decode("latin-1")
                             st.warning("File decoded using latin-1 encoding.")
                         except Exception as decode_err:
                             st.error(f"Could not decode TXT file. Error: {decode_err}")
                             file_text = None

                if file_text is not None:
                    if len(file_text) > MAX_CHAR_LIMIT:
                         st.error(f"Error: Uploaded file text ({len(file_text)} chars) exceeds limit ({MAX_CHAR_LIMIT}).")
                         st.session_state.uploaded_file_text = ""
                         st.session_state.uploaded_file_name = None
                         st.session_state.text_input = ""
                         st.session_state.active_source_info = DEFAULT_SOURCE_INFO
                    else:
                        st.success(f"✅ Extracted text from {uploaded_file.name}.")
                        st.session_state.uploaded_file_text = file_text
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.session_state.text_input = ""
                        st.session_state.image_description = ""
                        st.session_state.active_source_info = f"Using text from: {uploaded_file.name}"
                        st.session_state.conversion_complete = False
                        st.session_state.audio_data = None
                        st.session_state.camera_key = "camera_" + str(hash(uploaded_file.name))[:6]
                else:
                    # Extraction failed
                    st.session_state.uploaded_file_text = ""
                    st.session_state.uploaded_file_name = None
                    st.session_state.active_source_info = DEFAULT_SOURCE_INFO if not st.session_state.text_input else "Using typed text"
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.session_state.uploaded_file_text = ""
                st.session_state.uploaded_file_name = None
                st.session_state.active_source_info = DEFAULT_SOURCE_INFO if not st.session_state.text_input else "Using typed text"

    st.header("2. Select Voice")
    voice_selection = st.selectbox(
        "Choose a Lemonfox voice", options=list(VOICE_OPTIONS.keys()), index=0
    )
    selected_voice_key = VOICE_OPTIONS[voice_selection]

    st.header("3. Convert Text Input")
    text_for_main_button = ""
    if st.session_state.text_input and st.session_state.active_source_info != "Using text from analyzed image":
        text_for_main_button = st.session_state.text_input
    elif st.session_state.uploaded_file_text:
        text_for_main_button = st.session_state.uploaded_file_text
        # Check length just before conversion attempt as well
        if len(text_for_main_button) > MAX_CHAR_LIMIT:
             st.warning(f"Uploaded text exceeds limit ({len(text_for_main_button)}/{MAX_CHAR_LIMIT} chars). Cannot convert.")
             text_for_main_button = "" # Prevent conversion

    # Main Convert Button (check API key and text existence)
    main_button_disabled = not text_for_main_button or not LEMONFOX_API_KEY
    if st.button("Convert Text to Speech", type="primary", key="main_convert_button", disabled=main_button_disabled):
        audio_data = text_to_speech(text_for_main_button, selected_voice_key)
        if audio_data:
            st.session_state.audio_data = audio_data
            st.session_state.conversion_complete = True
        else:
            st.session_state.audio_data = None
            st.session_state.conversion_complete = False

# --- Column 2: Image Input and Audio Output ---
with col2:
    st.header("Audio Output")
    if st.session_state.conversion_complete and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format="audio/mp3")
        st.download_button("Download MP3", st.session_state.audio_data, "speech.mp3", "audio/mpeg")
    elif st.session_state.conversion_complete and not st.session_state.audio_data:
        st.error("Audio generation failed. Check input/API status.")
        st.session_state.conversion_complete = False

    st.header("Alternative Input: Image")

    # --- Image Capture ---
    with st.expander("📷 Capture Photo", expanded=False):
        captured_image_buffer = st.camera_input("Take a picture", key=st.session_state.camera_key)
        if captured_image_buffer is not None:
             if captured_image_buffer != st.session_state.captured_image:
                st.session_state.captured_image = captured_image_buffer
                st.session_state.uploaded_image = None
                st.image(captured_image_buffer, caption="Captured Photo", width=250)
                st.session_state.uploader_key = "uploader_" + str(hash(captured_image_buffer.getvalue()))[:6] # Reset other uploader

                # Describe and Speak Button (check both API keys)
                capture_button_disabled = not OPENAI_API_KEY or not LEMONFOX_API_KEY
                if st.button("Describe and Speak Captured Photo", key="speak_captured", disabled=capture_button_disabled):
                     img_bytes = captured_image_buffer.getvalue()
                     process_and_speak_image(img_bytes, selected_voice_key, is_upload=False)
                     st.rerun() # Rerun to reflect changes in text area and audio player

    # --- Image Upload ---
    with st.expander("🖼️ Upload Image", expanded=False):
        uploaded_image_file = st.file_uploader(
            "Upload an image (JPG, PNG, etc.)",
            type=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            key=st.session_state.uploader_key + "_img"
        )
        if uploaded_image_file is not None:
             if uploaded_image_file != st.session_state.uploaded_image:
                st.session_state.uploaded_image = uploaded_image_file
                st.session_state.captured_image = None
                st.image(uploaded_image_file, caption="Uploaded Image", width=250)
                st.session_state.camera_key = "camera_" + str(hash(uploaded_image_file.getvalue()))[:6] # Reset camera

                # Describe and Speak Button (check both API keys)
                upload_button_disabled = not OPENAI_API_KEY or not LEMONFOX_API_KEY
                if st.button("Describe and Speak Uploaded Image", key="speak_uploaded", disabled=upload_button_disabled):
                    img_bytes = uploaded_image_file.getvalue()
                    process_and_speak_image(img_bytes, selected_voice_key, is_upload=True)
                    st.rerun() # Rerun to reflect changes

# --- Footer ---
st.markdown("---")
st.caption(f"Accessible TTS Tool | Max text length: {MAX_CHAR_LIMIT} chars.")
st.caption("Requires OpenAI (image analysis) & Lemonfox (TTS) API keys in secrets.")

# --- Debugging (Optional: Remove in production) ---
# with st.expander("Debug Session State"):
#      st.json(st.session_state.to_dict())

# --- End of Updated Code ---
