import streamlit as st
import requests
import base64
import io

# --- Try importing backend functions ---
# Assume image_backend.py is in the same directory
# It should contain: look_at_photo(base64_image, upload=False) and encode_image_from_bytes(image_bytes)
try:
    from image_backend import look_at_photo, encode_image_from_bytes
    BACKEND_LOADED = True
except ImportError:
    st.error("FATAL ERROR: image_backend.py not found.")
    # Define dummy functions if import fails, app won't work but won't crash immediately
    def encode_image_from_bytes(byte_data): return None
    def look_at_photo(base64_image, upload=False): return "Error: Backend not loaded."
    BACKEND_LOADED = False

# --- Configuration & Constants ---
st.set_page_config(layout="wide") # Use wide layout

LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
TTS_MODEL = "tts-1"
# Use a fairly neutral voice, maybe Alloy or Nova? Adjust if needed.
DEFAULT_VOICE = "alloy"
MAX_CHAR_LIMIT = 4000 # Limit for description length for TTS

# --- API Keys Check (Essential) ---
missing_keys = []
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

if not OPENAI_API_KEY:
    missing_keys.append("OPENAI_API_KEY")
if not LEMONFOX_API_KEY:
    missing_keys.append("LEMONFOX_API_KEY")

# --- Custom CSS Injection ---
# This CSS aims to hide Streamlit UI elements and make buttons huge
# It might need tweaking depending on Streamlit versions and specific element structures.
# Inspect elements in your browser (Right-click -> Inspect) to find the right selectors if needed.
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp { padding: 1rem; } /* Reduce padding */

            /* Make Camera Input Button Huge */
            div[data-testid="stCameraInput"] > div > button {
                background-color: #008CBA; /* Blue */
                border: none;
                color: white;
                padding: 50px 50px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 48px; /* Large font */
                margin: 20px 2px;
                cursor: pointer;
                border-radius: 12px;
                width: 80vw; /* Very wide */
                height: 50vh; /* Very tall */
                line-height: 1.2; /* Adjust for text wrapping */
            }
            /* Hide the text label above camera button if needed */
            div[data-testid="stCameraInput"] label {
                 display: none;
            }

            /* Make Action Buttons Huge */
            div[data-testid="stButton"] > button {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 40px 40px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 40px;
                margin: 15px 2px;
                cursor: pointer;
                border-radius: 12px;
                width: 70vw; /* Wide */
                height: 25vh; /* Tall */
                 line-height: 1.2;
            }
            /* Specific style for Start Over button */
             div[data-testid="stButton"] > button[kind="secondary"] {
                 background-color: #f44336; /* Red */
             }

             /* Center elements vertically and horizontally */
             .stApp > div:first-child {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 95vh; /* Ensure centering takes vertical space */
             }
             /* Target the container holding the buttons/audio */
             div[data-testid="stVerticalBlock"] {
                 align-items: center !important; /* Force alignment */
             }


            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Helper Functions (TTS and Analysis) ---
def text_to_speech_simple(text, voice_key):
    """Simplified TTS call for this app."""
    if not LEMONFOX_API_KEY: return None, "TTS API Key missing."
    if not text: return None, "No text to speak."
    if len(text) > MAX_CHAR_LIMIT: return None, f"Text too long ({len(text)} > {MAX_CHAR_LIMIT})."

    headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
    data = {"model": TTS_MODEL, "input": text, "voice": voice_key, "response_format": "mp3"}

    try:
        # No spinner here for max simplicity, processing happens fast enough hopefully
        response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=45)
        response.raise_for_status()
        return response.content, None # Return audio data, no error
    except Exception as e:
        return None, f"TTS Error: {e}" # Return None, error message

def perform_image_analysis_simple(image_bytes):
    """Simplified image analysis call."""
    if not OPENAI_API_KEY: return None, "Analysis API Key missing."
    if not image_bytes: return None, "No image data."

    try:
        base64_image = encode_image_from_bytes(image_bytes)
        if not base64_image: return None, "Image encoding failed."
        # Force gpt-4o-mini for speed in this simple app, upload=False
        description = look_at_photo(base64_image, upload=False)

        if description and "error" not in description.lower() and "fail" not in description.lower():
            return description, None # Return description, no error
        else:
            return None, f"Analysis failed: {description or 'No response.'}" # Return None, error message
    except Exception as e:
        return None, f"Analysis Error: {e}" # Return None, error message

# --- Initialize Session State ---
if "photo_buffer" not in st.session_state:
    st.session_state.photo_buffer = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "show_play" not in st.session_state:
    st.session_state.show_play = False
if "camera_key" not in st.session_state:
    st.session_state.camera_key = "cam_initial" # Key for resetting camera

# --- Main App Logic ---

# Check for API keys first
if missing_keys or not BACKEND_LOADED:
    st.error(f"ERROR: App cannot run. Missing: {', '.join(missing_keys)}{' and image_backend.py' if not BACKEND_LOADED else ''}. Please configure secrets.")
    st.stop() # Halt execution

# State 1: Ready to take photo
if not st.session_state.show_play and not st.session_state.processing:
    st.session_state.error_message = None # Clear previous errors
    captured_image_buffer = st.camera_input(
        "Tap HUGE button to take photo", # Label won't show due to CSS, but good practice
        key=st.session_state.camera_key,
        label_visibility="hidden" # Attempt to hide label explicitly
        )

    if captured_image_buffer is not None:
        st.session_state.photo_buffer = captured_image_buffer.getvalue()
        st.session_state.processing = True
        st.rerun() # Go to processing state

# State 2: Processing photo
elif st.session_state.processing:
    with st.spinner("Thinking..."): # Simple feedback
        description, analysis_error = perform_image_analysis_simple(st.session_state.photo_buffer)
        st.session_state.photo_buffer = None # Clear buffer

        if analysis_error:
            st.session_state.error_message = analysis_error
            st.session_state.processing = False
            st.session_state.show_play = False # Go back to camera state on error
            st.rerun()
        else:
            audio_data, tts_error = text_to_speech_simple(description, DEFAULT_VOICE)
            if tts_error:
                st.session_state.error_message = tts_error
                st.session_state.processing = False
                st.session_state.show_play = False # Go back to camera state on error
                st.rerun()
            else:
                # SUCCESS! Store audio, switch state
                st.session_state.audio_data = audio_data
                st.session_state.processing = False
                st.session_state.show_play = True
                st.rerun()

# State 3: Show Play button and Audio
elif st.session_state.show_play:
    # Display the huge "Play" button first
    st.button("▶️ PLAY AUDIO", key="play_dummy") # This button doesn't *do* anything except be a big target

    # Display the actual audio player
    if st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format="audio/mp3")
    else:
        st.error("Error: Audio data is missing.") # Should not happen if logic is correct

    # Display a huge "Start Over" button
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        # Reset state variables to initial values
        st.session_state.photo_buffer = None
        st.session_state.processing = False
        st.session_state.audio_data = None
        st.session_state.error_message = None
        st.session_state.show_play = False
        # Important: Change camera key to force reset
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}"
        st.rerun()

# Display errors if they occurred in processing
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    # Add a button to acknowledge error and reset?
    if st.button("Try Again"):
         st.session_state.error_message = None
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}" # Reset camera on error ack
         st.rerun()
