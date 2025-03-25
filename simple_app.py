import streamlit as st
import requests
import base64
import io

# --- Try importing backend functions ---
try:
    from image_backend import look_at_photo, encode_image_from_bytes
    BACKEND_LOADED = True
except ImportError:
    st.error("FATAL ERROR: image_backend.py not found.")
    def encode_image_from_bytes(byte_data): return None
    def look_at_photo(base64_image, upload=False): return "Error: Backend not loaded."
    BACKEND_LOADED = False

# --- Configuration & Constants ---
st.set_page_config(layout="wide")

LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
TTS_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
MAX_CHAR_LIMIT = 4000

# --- API Keys Check ---
missing_keys = []
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

if not OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY")
if not LEMONFOX_API_KEY: missing_keys.append("LEMONFOX_API_KEY")

# --- Custom CSS Injection (Hover fix should be okay) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp { padding: 1rem; }

            /* Make Camera Input Button Huge */
            .camera-button {
                background-color: #008CBA; border: none; color: white; padding: 50px 50px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 48px; margin: 20px 2px; cursor: pointer;
                border-radius: 12px; width: 80vw; height: 50vh; line-height: 1.2;
            }
            .camera-button:hover { color: white !important; opacity: 0.9; }

            /* General Style for Streamlit Action Buttons (Start Over / Try Again) */
            div[data-testid="stButton"] > button {
                border: none; color: white; padding: 40px 40px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 40px; margin: 15px 2px; cursor: pointer;
                border-radius: 12px; width: 70vw; /* Keep width */
                min-height: 15vh; /* Use min-height for flexibility */
                line-height: 1.2; box-sizing: border-box; /* Ensure padding included */
                display: flex !important; /* Use flex to center content vertically */
                align-items: center !important;
                justify-content: center !important;
            }
            div[data-testid="stButton"] > button:hover { color: white !important; opacity: 0.9; }
            div[data-testid="stButton"] > button[kind="secondary"] { background-color: #f44336; /* Red */ }
            div[data-testid="stButton"] > button[kind="secondary"]:hover { background-color: #d32f2f; color: white !important; opacity: 1.0; }

             /* Centering */
             .stApp > div:first-child {
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: 95vh;
             }
             /* Target containers for centering content */
             div[data-testid="stVerticalBlock"],
             div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
             div[data-streamlit-component-button-audio] { /* Target our component wrapper */
                 align-items: center !important;
                 display: flex !important;
                 flex-direction: column !important;
                 justify-content: center !important;
                 width: 100% !important; /* Ensure component takes space */
             }
             /* Add some gap AFTER the component IF NEEDED - adjust as necessary */
             div[data-streamlit-component-button-audio] + div[data-testid="element-container"] {
                  margin-top: 20px; /* Space before the Start Over button */
             }
            .camera-preview {
                max-height: 300px;
                max-width: 80vw;
                overflow: hidden;
            }

            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Helper Functions (TTS and Analysis - unchanged) ---
def text_to_speech_simple(text, voice_key):
    if not LEMONFOX_API_KEY: return None, "TTS API Key missing."
    if not text: return None, "No text to speak."
    if len(text) > MAX_CHAR_LIMIT: return None, f"Text too long ({len(text)} > {MAX_CHAR_LIMIT})."
    headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
    data = {"model": TTS_MODEL, "input": text, "voice": voice_key, "response_format": "mp3"}
    try:
        response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=45)
        response.raise_for_status()
        return response.content, None
    except Exception as e: return None, f"TTS Error: {e}"

def perform_image_analysis_simple(image_bytes):
    if not OPENAI_API_KEY: return None, "Analysis API Key missing."
    if not image_bytes: return None, "No image data."
    try:
        base64_image = encode_image_from_bytes(image_bytes)
        if not base64_image: return None, "Image encoding failed."
        description = look_at_photo(base64_image, upload=False)
        if description and "error" not in description.lower() and "fail" not in description.lower():
            return description, None
        else: return None, f"Analysis failed: {description or 'No response.'}"
    except Exception as e: return None, f"Analysis Error: {e}"

# --- Initialize Session State ---
if "photo_buffer" not in st.session_state: st.session_state.photo_buffer = None
if "processing" not in st.session_state: st.session_state.processing = False
if "audio_data" not in st.session_state: st.session_state.audio_data = None
if "error_message" not in st.session_state: st.session_state.error_message = None
if "show_play" not in st.session_state: st.session_state.show_play = False
if "camera_key" not in st.session_state: st.session_state.camera_key = "cam_initial"

# --- Main App Logic ---

if missing_keys or not BACKEND_LOADED:
    st.error(f"ERROR: App cannot run. Missing: {', '.join(missing_keys)}{' and image_backend.py' if not BACKEND_LOADED else ''}.")
    st.stop()

# State 1: Ready to take photo
if not st.session_state.show_play and not st.session_state.processing:
    st.session_state.error_message = None
    if st.button("TAKE PICTURE", key="take_photo", type="primary", help="Tap HUGE button to take photo",  use_container_width=True,  css={"width":"80vw", "height": "50vh", "font-size":"48px"}, classes = ["camera-button"]):
        st.session_state.photo_buffer = st.camera_input(
            "", key=st.session_state.camera_key, label_visibility="hidden"
        ).getvalue() if st.camera_input(
            "", key=st.session_state.camera_key, label_visibility="hidden"
        ) is not None else None
        if st.session_state.photo_buffer is not None:
            st.session_state.processing = True
            st.rerun()

    if st.camera_input("", key=st.session_state
