import streamlit as st
import requests
import base64
import PyPDF2
import docx
import io

# Import functions from image_backend.py
try:
    from image_backend import look_at_photo, encode_image_from_bytes
except ImportError:
    st.error("🚨 FATAL ERROR: image_backend.py not found. Image analysis features will fail.")
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
MAX_CHAR_LIMIT = 10000
DEFAULT_SOURCE_INFO = "Enter text, upload a file, or use an image."

# Constants for Radio Button Options
IMAGE_MODE_TEXT_FIRST = "Process image into text first"
IMAGE_MODE_IMMEDIATE_SPEECH = "Immediately process image into speech"
IMAGE_PROCESSING_MODES = [IMAGE_MODE_TEXT_FIRST, IMAGE_MODE_IMMEDIATE_SPEECH]


# --- API Keys Check ---
missing_keys = []
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

if not OPENAI_API_KEY:
    missing_keys.append("OPENAI_API_KEY (for image analysis)")
if not LEMONFOX_API_KEY:
    missing_keys.append("LEMONFOX_API_KEY (for text-to-speech)")

if missing_keys:
    keys_str = " and ".join(missing_keys)
    st.error(f"🚨 Error: API Key(s) not found: {keys_str}. Related features disabled.")

# --- Helper Functions (extract_text_from_pdf, extract_text_from_docx - unchanged) ---
def extract_text_from_pdf(file_bytes_io):
    try:
        pdf_reader = PyPDF2.PdfReader(file_bytes_io)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text: text += page_text + "\n\n"
        return text
    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF: Corrupted or encrypted? ({e})")
        return None
    except Exception as e:
        st.error(f"PDF processing error: {e}")
        return None

def extract_text_from_docx(file_bytes_io):
    try:
        doc = docx.Document(file_bytes_io)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return None

# --- Helper Function: text_to_speech ---
def text_to_speech(text, voice_key):
    """Converts text to speech using the Lemonfox API."""
    if not LEMONFOX_API_KEY:
        st.error("Cannot convert: Lemonfox API Key missing.")
        return None
    if not text:
        st.warning("Cannot convert empty text.")
        return None
    if len(text) > MAX_CHAR_LIMIT:
        st.error(f"Error: Text ({len(text)} chars) exceeds limit ({MAX_CHAR_LIMIT}).")
        return None

    headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
    data = {"model": TTS_MODEL, "input": text, "voice": voice_key, "response_format": "mp3"}

    try:
        with st.spinner("🔊 Generating speech (Lemonfox)..."):
            response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
            response.raise_for_status()
        st.success("✅ Speech generated!")
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Lemonfox API Error: {e}")
        return None
    except Exception as e:
        st.error(f"TTS conversion error: {e}")
        return None

# --- Helper Function: perform_image_analysis ---
def perform_image_analysis(image_bytes, is_upload):
    """Analyzes image using OpenAI and returns the description or None on error."""
    if not OPENAI_API_KEY:
         st.error("Cannot analyze: OpenAI API Key missing.")
         return None
    try:
        with st.spinner("🖼️ Analyzing image (OpenAI)..."):
            base64_image = encode_image_from_bytes(image_bytes)
            description = look_at_photo(base64_image, upload=is_upload)

        if description and "error" not in description.lower() and "fail" not in description.lower():
            st.success("✅ Image analyzed.")
            return description
        else:
            st.error(f"Image analysis failed: {description or 'No description returned.'}")
            return None
    except Exception as e:
        st.error(f"Error during image analysis call: {e}")
        return None

# --- Initialize Session State ---
default_values = {
    "text_input": "", "uploaded_file_text": "", "uploaded_file_name": None,
    "image_description": "", "audio_data": None, "conversion_complete": False,
    "active_source_info": DEFAULT_SOURCE_INFO, "captured_image": None,
    "uploaded_image": None, "camera_key": "camera_1", "uploader_key": "uploader_1",
    "processed_file_name": None,
    "image_processing_mode": IMAGE_MODE_TEXT_FIRST # Default image mode
}
for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Main App Layout ---
st.title("Accessible Text-to-Speech 🔊")
col1, col2 = st.columns([3, 2])

# --- Column 1: Text Input, File Upload, Controls ---
with col1:
    st.header("1. Provide Text")
    st.info(f"**Source:** {st.session_state.active_source_info}")

    # Text input area
    current_text_in_box = st.text_area(
        "Type, paste, or describe image here", height=250,
        value=st.session_state.text_input, # Display current state
        key="text_area_main",
        help=f"Max {MAX_CHAR_LIMIT} chars for TTS."
    )
    if current_text_in_box != st.session_state.text_input:
         st.session_state.text_input = current_text_in_box
         if current_text_in_box:
             st.session_state.active_source_info = "Using typed text"
             st.session_state.conversion_complete = False
             st.session_state.audio_data = None
         elif not st.session_state.uploaded_file_text and not st.session_state.image_description:
             st.session_state.active_source_info = DEFAULT_SOURCE_INFO

    st.subheader("Or Upload Text File")
    uploaded_file = st.file_uploader(
        "Upload (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"],
        help=f"Max text length: {MAX_CHAR_LIMIT} chars.",
        key=st.session_state.uploader_key
    )

    # Process uploaded text file
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.get('processed_file_name', None):
            st.session_state.processed_file_name = uploaded_file.name
            st.write(f"Processing file: `{uploaded_file.name}`")
            file_text = None
            try:
                # (File extraction logic remains the same)
                bytes_data = io.BytesIO(uploaded_file.getvalue())
                if uploaded_file.name.lower().endswith('.pdf'): file_text = extract_text_from_pdf(bytes_data)
                elif uploaded_file.name.lower().endswith('.docx'): file_text = extract_text_from_docx(bytes_data)
                elif uploaded_file.name.lower().endswith('.txt'):
                    try: file_text = bytes_data.getvalue().decode("utf-8")
                    except UnicodeDecodeError:
                        try: file_text = bytes_data.getvalue().decode("latin-1"); st.warning("Decoded TXT as Latin-1.")
                        except: file_text = None; st.error("Cannot decode TXT file.")

                if file_text is not None:
                    if len(file_text) > MAX_CHAR_LIMIT:
                         st.error(f"File text ({len(file_text)} chars) exceeds limit ({MAX_CHAR_LIMIT}).")
                         st.session_state.uploaded_file_text = ""; st.session_state.uploaded_file_name = None
                    else:
                        # SUCCESSFUL TEXT FILE -> Update state
                        st.session_state.uploaded_file_text = file_text
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.session_state.text_input = file_text # Display file text in box
                        st.session_state.image_description = ""; st.session_state.captured_image = None; st.session_state.uploaded_image = None # Clear image stuff
                        st.session_state.active_source_info = f"Using text from: {uploaded_file.name}"
                        st.session_state.conversion_complete = False; st.session_state.audio_data = None
                        st.session_state.camera_key = "cam_" + str(hash(uploaded_file.name))[:4] # Reset camera
                        st.rerun()
                else: # File text extraction failed
                    st.session_state.uploaded_file_text = ""; st.session_state.uploaded_file_name = None
                    if not st.session_state.text_input: st.session_state.active_source_info = DEFAULT_SOURCE_INFO
            except Exception as e:
                st.error(f"Error processing file: {e}")
                st.session_state.uploaded_file_text = ""; st.session_state.uploaded_file_name = None
                if not st.session_state.text_input: st.session_state.active_source_info = DEFAULT_SOURCE_INFO

    st.header("2. Select Voice & Convert")
    voice_selection = st.selectbox(
        "Choose Lemonfox voice", options=list(VOICE_OPTIONS.keys()), index=0, key="voice_selector"
    )
    # Get the selected voice key HERE, so it's available for Column 2 processing
    selected_voice_key = VOICE_OPTIONS[voice_selection]

    # Main Convert Button
    text_to_convert_now = st.session_state.text_input
    convert_button_disabled = not text_to_convert_now or not LEMONFOX_API_KEY
    if st.button("Convert Text Box to Speech", type="primary", key="main_convert_button", disabled=convert_button_disabled):
        # Call TTS using the selected voice from above
        audio_data = text_to_speech(text_to_convert_now, selected_voice_key)
        if audio_data:
            st.session_state.audio_data = audio_data
            st.session_state.conversion_complete = True
        else:
            st.session_state.audio_data = None
            st.session_state.conversion_complete = False
        # Rerun might be needed IF the audio player doesn't always update automatically
        # st.rerun()


# --- Column 2: Image Input and Audio Output ---
with col2:
    st.header("Audio Output")
    if st.session_state.conversion_complete and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format="audio/mp3")
        st.download_button("Download MP3", st.session_state.audio_data, "speech.mp3", "audio/mpeg")
    elif st.session_state.conversion_complete and not st.session_state.audio_data:
        # Display error if conversion was triggered but failed
        st.error("Audio generation failed. Check input/API status.")
        st.session_state.conversion_complete = False # Reset flag


    st.header("Alternative Input: Image")

    # --- Image Processing Mode Selection ---
    st.radio(
        "Image Handling:",
        options=IMAGE_PROCESSING_MODES,
        key="image_processing_mode", # Links to session state
        horizontal=True, # Display options side-by-side
        help="Choose whether to generate text only, or generate text and then immediately convert it to speech."
    )


    # --- Image Capture ---
    with st.expander("📷 Capture Photo", expanded=False):
        captured_image_buffer = st.camera_input("Take a picture", key=st.session_state.camera_key)

        if captured_image_buffer is not None:
             if captured_image_buffer != st.session_state.captured_image:
                st.session_state.captured_image = captured_image_buffer
                st.session_state.uploaded_image = None
                st.image(captured_image_buffer, caption="Captured Photo", width=250)
                st.session_state.uploader_key = "uploader_" + str(hash(captured_image_buffer.getvalue()))[:6] # Reset file uploader

                # --- IMMEDIATE ANALYSIS ---
                img_bytes = captured_image_buffer.getvalue()
                description = perform_image_analysis(img_bytes, is_upload=False)

                if description:
                    # Always update text state first
                    st.session_state.text_input = description
                    st.session_state.image_description = description
                    st.session_state.uploaded_file_text = ""
                    st.session_state.uploaded_file_name = None
                    st.session_state.active_source_info = "Using text from analyzed image"
                    st.session_state.conversion_complete = False # Reset audio initially
                    st.session_state.audio_data = None

                    # --- Conditional TTS Call ---
                    if st.session_state.image_processing_mode == IMAGE_MODE_IMMEDIATE_SPEECH:
                        st.write("Immediately generating speech for captured photo...") # User feedback
                        # Use the voice selected in Column 1
                        audio_data = text_to_speech(description, selected_voice_key)
                        if audio_data:
                            st.session_state.audio_data = audio_data
                            st.session_state.conversion_complete = True
                        # Errors handled within text_to_speech

                    # Rerun to update text box display and potentially the audio player
                    st.rerun()


    # --- Image Upload ---
    with st.expander("🖼️ Upload Image", expanded=False):
        uploaded_image_file = st.file_uploader(
            "Upload (JPG, PNG, etc.)",
            type=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            key=st.session_state.uploader_key + "_img"
        )

        if uploaded_image_file is not None:
             if uploaded_image_file != st.session_state.uploaded_image:
                st.session_state.uploaded_image = uploaded_image_file
                st.session_state.captured_image = None
                st.image(uploaded_image_file, caption="Uploaded Image", width=250)
                st.session_state.camera_key = "camera_" + str(hash(uploaded_image_file.getvalue()))[:6] # Reset camera

                # --- IMMEDIATE ANALYSIS ---
                img_bytes = uploaded_image_file.getvalue()
                description = perform_image_analysis(img_bytes, is_upload=True)

                if description:
                    # Always update text state first
                    st.session_state.text_input = description
                    st.session_state.image_description = description
                    st.session_state.uploaded_file_text = ""
                    st.session_state.uploaded_file_name = None
                    st.session_state.active_source_info = "Using text from analyzed image"
                    st.session_state.conversion_complete = False # Reset audio initially
                    st.session_state.audio_data = None

                    # --- Conditional TTS Call ---
                    if st.session_state.image_processing_mode == IMAGE_MODE_IMMEDIATE_SPEECH:
                        st.write("Immediately generating speech for uploaded image...") # User feedback
                        # Use the voice selected in Column 1
                        audio_data = text_to_speech(description, selected_voice_key)
                        if audio_data:
                            st.session_state.audio_data = audio_data
                            st.session_state.conversion_complete = True
                        # Errors handled within text_to_speech

                    # Rerun to update text box display and potentially the audio player
                    st.rerun()


# --- Footer ---
st.markdown("---")
st.caption(f"Accessible TTS Tool | Max text: {MAX_CHAR_LIMIT} chars.")
st.caption("Requires OpenAI & Lemonfox API keys in secrets.")

# --- Debugging ---
# with st.expander("Debug Session State"):
#      st.json(st.session_state.to_dict())
