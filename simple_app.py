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

# --- Custom CSS Injection (Revised for Separate Button) ---
hide_streamlit_style = f"""
            <style>
            #MainMenu {{visibility: hidden;}}
            header {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            .stApp {{ padding: 1rem; }}

            /* Style for the CUSTOM 'Activate Camera' button */
            /* Use a unique key/class if possible, or target by position/order if needed */
            /* Targeting the first button within the main block */
             div[data-testid="stVerticalBlock"] > div:first-child > div[data-testid="stButton"] > button {{
                 background-color: #008CBA; /* Blue */
                 border: none; color: white; padding: 50px 50px;
                 text-align: center; text-decoration: none; display: inline-block;
                 font-size: 48px; margin: 20px 2px; cursor: pointer;
                 border-radius: 12px; width: 80vw; height: 50vh; line-height: 1.2;
                 box-sizing: border-box;
                 /* Ensure it's centered if container uses flex */
                 display: flex !important; align-items: center !important; justify-content: center !important;
             }}
             div[data-testid="stVerticalBlock"] > div:first-child > div[data-testid="stButton"] > button:hover {{
                  color: white !important; opacity: 0.9;
             }}


            /* Standard Camera Input - Keep it relatively normal size or hide if needed */
            /* We are NOT styling the button inside stCameraInput anymore */
            div[data-testid="stCameraInput"] {{
                 margin-top: 20px; /* Add space below the activate button (if shown) */
                 display: flex; /* Center the camera widget itself */
                 justify-content: center;
            }}
             /* Optionally hide the label for the standard camera input */
            div[data-testid="stCameraInput"] label {{
                 /* display: none; */ /* Can hide if it looks cleaner */
            }}


            /* General Style for Streamlit Action Buttons (Start Over / Try Again) */
            /* Make these selectors slightly more specific if needed */
            /* Targeting buttons that are NOT the first one (Activate Camera) */
            div[data-testid="stVerticalBlock"] > div:not(:first-child) > div[data-testid="stButton"] > button,
            div[data-testid="stVerticalBlock"] > div[data-testid="stButton"]:not(:first-child) > button {{
                border: none; color: white; padding: 40px 40px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 40px; margin: 15px 2px; cursor: pointer;
                border-radius: 12px; width: 70vw;
                min-height: 15vh; line-height: 1.2; box-sizing: border-box;
                display: flex !important; align-items: center !important; justify-content: center !important;
            }}
            /* Make Start Over button taller & Red */
            div[data-testid="stButton"] > button[kind="secondary"] {{ /* Keep targeting specific kind */
                 background-color: #f44336 !important; /* Red */
                 height: 25vh; min-height: 25vh;
            }}
            /* Ensure Try Again button is Green */
             div[data-testid="stVerticalBlock"] > div:not(:first-child) > div[data-testid="stButton"] > button:not([kind="secondary"]),
             div[data-testid="stVerticalBlock"] > div[data-testid="stButton"]:not(:first-child) > button:not([kind="secondary"]) {{
                 background-color: #4CAF50; /* Green */
             }}

            /* Hover states for Start Over / Try Again */
            div[data-testid="stVerticalBlock"] > div:not(:first-child) > div[data-testid="stButton"] > button:hover,
            div[data-testid="stVerticalBlock"] > div[data-testid="stButton"]:not(:first-child) > button:hover {{
                 color: white !important; opacity: 0.9;
            }}
            div[data-testid="stButton"] > button[kind="secondary"]:hover {{ background-color: #d32f2f !important; opacity: 1.0; }}
             div[data-testid="stVerticalBlock"] > div:not(:first-child) > div[data-testid="stButton"] > button:not([kind="secondary"]):hover,
             div[data-testid="stVerticalBlock"] > div[data-testid="stButton"]:not(:first-child) > button:not([kind="secondary"]):hover {{
                 background-color: #45a049; /* Darker Green */
             }}


             /* Centering */
             .stApp > div:first-child {{
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: 95vh;
             }}
             div[data-testid="stVerticalBlock"],
             div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
             div[data-streamlit-component-button-audio] {{
                 align-items: center !important; display: flex !important;
                 flex-direction: column !important; justify-content: center !important;
                 width: 100% !important;
             }}
             div[data-streamlit-component-button-audio] {{ margin-bottom: 20px; }}
             div[data-testid="stButton"] {{ margin-bottom: 10px; }}

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
        if description and "error" not in description.lower() and "fail" in description.lower():
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
# --- NEW STATE VARIABLE ---
if "show_camera_widget" not in st.session_state: st.session_state.show_camera_widget = False

# --- Main App Logic ---

if missing_keys or not BACKEND_LOADED:
    st.error(f"ERROR: App cannot run. Missing: {', '.join(missing_keys)}{' and image_backend.py' if not BACKEND_LOADED else ''}.")
    st.stop()

# State 1A: Show Giant Activate Button
if not st.session_state.show_camera_widget and not st.session_state.show_play and not st.session_state.processing:
    st.session_state.error_message = None # Clear error
    # Use a unique key for this specific button if CSS selector fails
    if st.button("📷 Activate Camera & Take Photo", key="activate_cam_button"):
        st.session_state.show_camera_widget = True
        st.rerun()

# State 1B: Show Camera Widget
elif st.session_state.show_camera_widget and not st.session_state.show_play and not st.session_state.processing:
    st.info("Camera activated. Use the control below to take the picture.") # Optional feedback
    captured_image_buffer = st.camera_input(
        "Camera Feed", # Standard label, maybe hide with CSS later if needed
        key=st.session_state.camera_key,
        label_visibility="visible" # Or "collapsed"
        )
    if captured_image_buffer is not None:
        st.session_state.photo_buffer = captured_image_buffer.getvalue()
        st.session_state.processing = True
        st.session_state.show_camera_widget = False # Hide camera widget for next stage
        st.rerun()

# State 2: Processing photo
elif st.session_state.processing:
    # This state remains the same
    with st.spinner("Thinking..."):
        description, analysis_error = perform_image_analysis_simple(st.session_state.photo_buffer)
        st.session_state.photo_buffer = None
        if analysis_error:
            st.session_state.error_message = analysis_error
            st.session_state.processing = False; st.session_state.show_play = False; st.session_state.show_camera_widget = False # Reset fully
            st.rerun()
        else:
            audio_data, tts_error = text_to_speech_simple(description, DEFAULT_VOICE)
            if tts_error:
                st.session_state.error_message = tts_error
                st.session_state.processing = False; st.session_state.show_play = False; st.session_state.show_camera_widget = False # Reset fully
                st.rerun()
            else:
                st.session_state.audio_data = audio_data
                st.session_state.processing = False; st.session_state.show_play = True; st.session_state.show_camera_widget = False # Set show_play
                st.rerun()

# State 3: Show Play button (HTML Component) and Audio
elif st.session_state.show_play:
    # This state remains largely the same
    if st.session_state.audio_data:
        audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
        audio_src = f"data:audio/mpeg;base64,{audio_base64}"
        # HTML Component (unchanged)
        component_html = f"""<style>...</style><div class="center-container" data-streamlit-component-button-audio>...</div><script>...</script>""" # Keep your working HTML/JS
        st.components.v1.html(component_html, height=300)
    else:
        st.error("Error: Audio data is missing.")

    # "Start Over" Button
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        # Reset state variables
        st.session_state.photo_buffer = None; st.session_state.processing = False
        st.session_state.audio_data = None; st.session_state.error_message = None
        st.session_state.show_play = False; st.session_state.show_camera_widget = False # Reset new flag too
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}"
        st.rerun()

# Error Display Logic
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    if st.button("Try Again"):
         st.session_state.error_message = None
         st.session_state.show_camera_widget = False # Go back to activate button
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}"
         st.rerun()
