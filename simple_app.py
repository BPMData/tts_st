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

# --- Custom CSS Injection (Reverted video rule, kept button resize) ---
# Using the CSS from the step before the video resize attempt
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp > div:first-child > div:first-child > div:first-child { padding: 1rem 1rem 0 1rem; }
            .stApp { padding: 0rem; }


            /* --- Camera Input Button (Slightly Larger) --- */
            div[data-testid="stCameraInput"] > div > button {
                background-color: #008CBA; border: none; color: white;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 24px; margin: 10px 2px 15px 2px; /* Adjusted margin */
                cursor: pointer; border-radius: 10px;
                width: 60vw; max-width: 400px;
                height: 15vh; min-height: 80px;
                padding: 15px 20px; line-height: 1.3; box-sizing: border-box;
                 display: block; margin-left: auto; margin-right: auto;
            }
            div[data-testid="stCameraInput"] > div > button:hover { color: white !important; opacity: 0.9; }
            div[data-testid="stCameraInput"] label { display: none; }

             /* REMOVED Video constraint rule */

             /* Center the camera widget container */
             div[data-testid="stCameraInput"] {
                  width: 100%; display: flex; justify-content: center;
                  flex-direction: column; align-items: center;
             }


            /* General Style for OTHER Action Buttons (Play/Start Over/Try Again) - Kept Large */
            #playButton {{ /* Play Button (Inside Component) */
                background-color: #4CAF50; border: none; color: white; text-align: center; text-decoration: none; display: block;
                font-size: 40px; margin: 15px auto; cursor: pointer; border-radius: 12px;
                width: 70vw; height: 25vh; line-height: 25vh; box-sizing: border-box; padding: 0;
            }}
            #playButton:hover {{ color: white !important; background-color: #45a049; }}

            div[data-testid="stButton"] > button { /* Start Over / Try Again Buttons */
                border: none; color: white; padding: 40px 40px; text-align: center; text-decoration: none; display: inline-block;
                font-size: 40px; margin: 15px 2px; cursor: pointer; border-radius: 12px; width: 70vw;
                min-height: 15vh; line-height: 1.2; box-sizing: border-box;
                display: flex !important; align-items: center !important; justify-content: center !important;
            }
            div[data-testid="stButton"] > button[kind="secondary"] { /* Start Over */
                 background-color: #f44336 !important; height: 25vh; min-height: 25vh;
            }
             div[data-testid="stButton"] > button:not([kind="secondary"]) { /* Try Again */
                 background-color: #4CAF50 !important; /* Ensure Green */
            }
             /* Hover states for Start Over / Try Again */
            div[data-testid="stButton"] > button:hover { color: white !important; opacity: 0.9; }
            div[data-testid="stButton"] > button[kind="secondary"]:hover { background-color: #d32f2f !important; opacity: 1.0; }
            div[data-testid="stButton"] > button:not([kind="secondary"]):hover { background-color: #45a049 !important; }


             /* Centering structure */
             .stApp > div:first-child { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 95vh; }
             div[data-testid="stVerticalBlock"], div[data-testid="stVerticalBlock"] > div[data-testid="element-container"], div[data-streamlit-component-button-audio] {
                 align-items: center !important; display: flex !important; flex-direction: column !important; justify-content: center !important; width: 100% !important;
             }
             div[data-streamlit-component-button-audio] { margin-bottom: 20px; }
             div[data-testid="stButton"] { margin-bottom: 10px; }

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
# --- NEW STATE ---
if "image_just_captured" not in st.session_state: st.session_state.image_just_captured = False


# --- Main App Logic ---

if missing_keys or not BACKEND_LOADED:
    st.error(f"ERROR: App cannot run. Missing: {', '.join(missing_keys)}{' and image_backend.py' if not BACKEND_LOADED else ''}.")
    st.stop()

# --- NEW: Check if an image was captured in the *previous* run ---
if st.session_state.image_just_captured and st.session_state.photo_buffer:
    st.session_state.image_just_captured = False # Reset flag
    st.session_state.processing = True # NOW trigger processing
    # No rerun here, allow script to continue into processing block below

# State 1: Ready to take photo
if not st.session_state.show_play and not st.session_state.processing:
    st.session_state.error_message = None
    # Prevent camera input from showing if we are about to process
    if not st.session_state.processing:
        captured_image_buffer = st.camera_input(
            "Take Photo", key=st.session_state.camera_key, label_visibility="hidden"
            )
        # Check if the buffer is newly available *compared to session state*
        if captured_image_buffer is not None and st.session_state.photo_buffer is None:
            st.session_state.photo_buffer = captured_image_buffer.getvalue()
            st.session_state.image_just_captured = True # Set flag
            # Don't set processing = True here, let the next rerun handle it
            st.rerun() # Rerun immediately after capture

# State 2: Processing photo
elif st.session_state.processing:
    with st.spinner("Thinking..."):
        # Make sure we use the buffer stored in session state
        img_bytes_to_process = st.session_state.photo_buffer
        st.session_state.photo_buffer = None # Clear buffer now we're using it

        if img_bytes_to_process: # Check if buffer actually has data
            description, analysis_error = perform_image_analysis_simple(img_bytes_to_process)
            if analysis_error:
                st.session_state.error_message = analysis_error
                st.session_state.processing = False; st.session_state.show_play = False
                st.rerun()
            else:
                audio_data, tts_error = text_to_speech_simple(description, DEFAULT_VOICE)
                if tts_error:
                    st.session_state.error_message = tts_error
                    st.session_state.processing = False; st.session_state.show_play = False
                    st.rerun()
                else:
                    st.session_state.audio_data = audio_data
                    st.session_state.processing = False; st.session_state.show_play = True
                    st.rerun()
        else:
            # Should not happen if logic is correct, but handle it
            st.session_state.error_message = "Error: Image data lost before processing."
            st.session_state.processing = False; st.session_state.show_play = False
            st.rerun()


# State 3: Show Play button (using HTML Component) and Audio
elif st.session_state.show_play:
    # This state remains the same
    if st.session_state.audio_data:
        audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
        audio_src = f"data:audio/mpeg;base64,{audio_base64}"
        # HTML Component (unchanged)
        component_html = f"""
        <style> /* Component-internal styles */ ... </style>
        <div class="center-container" data-streamlit-component-button-audio> ... </div>
        <script> /* JS remains the same */ ... </script>
        """ # Keep your working HTML/JS/CSS for component
        st.components.v1.html(component_html, height=300)
    else:
        st.error("Error: Audio data is missing.")

    # "Start Over" Button
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        st.session_state.photo_buffer = None; st.session_state.processing = False; st.session_state.audio_data = None
        st.session_state.error_message = None; st.session_state.show_play = False
        st.session_state.image_just_captured = False # Reset flag
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}"
        st.rerun()

# Error Display Logic
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    if st.button("Try Again"):
         st.session_state.error_message = None
         st.session_state.image_just_captured = False # Reset flag
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}"
         st.rerun()
