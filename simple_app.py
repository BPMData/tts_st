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

# --- Custom CSS Injection ---
# CHANGES: Removed ALL stCameraInput specific CSS. Adjusted default stButton style.
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp { padding: 1rem; }

            /* --- REMOVED ALL CSS for div[data-testid="stCameraInput"] --- */
            /* --- Let st.camera_input render with default Streamlit styles --- */


            /* General Style for Streamlit Action Buttons (TAKE PICTURE / Start Over / Try Again) */
            div[data-testid="stButton"] > button {
                background-color: #008CBA; /* Default BLUE for primary buttons */
                border: none; color: white; padding: 40px 40px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 40px; margin: 15px 2px; cursor: pointer;
                border-radius: 12px; width: 70vw;
                min-height: 15vh;
                line-height: 1.2; box-sizing: border-box;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            /* Hover for ALL buttons */
            div[data-testid="stButton"] > button:hover { color: white !important; opacity: 0.9; }

            /* Style for SECONDARY buttons (like Start Over, Try Again) */
            div[data-testid="stButton"] > button[kind="secondary"] {
                 background-color: #f44336; /* Red */
            }
            div[data-testid="stButton"] > button[kind="secondary"]:hover {
                 background-color: #d32f2f; color: white !important; opacity: 1.0;
            }

            /* Centering - Unchanged */
             .stApp > div:first-child {
                 display: flex; flex-direction: column; align-items: center;
                 justify-content: center; min-height: 95vh;
             }
             /* Target containers for centering content - Unchanged */
             div[data-testid="stVerticalBlock"],
             div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
             div[data-streamlit-component-button-audio] {
                  align-items: center !important;
                  display: flex !important;
                  flex-direction: column !important;
                  justify-content: center !important;
                  width: 100% !important;
             }
             div[data-streamlit-component-button-audio] + div[data-testid="element-container"] {
                   margin-top: 20px;
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
# NEW state variable to control camera visibility
if "show_camera" not in st.session_state: st.session_state.show_camera = False

# --- Main App Logic ---

if missing_keys or not BACKEND_LOADED:
    st.error(f"ERROR: App cannot run. Missing: {', '.join(missing_keys)}{' and image_backend.py' if not BACKEND_LOADED else ''}.")
    st.stop()

# State 1: Show Big Button OR Camera Input
if not st.session_state.show_play and not st.session_state.processing:
    st.session_state.error_message = None # Clear errors when returning to this state

    # Condition: Show Big Button first
    if not st.session_state.show_camera:
        # Use st.button, it will inherit the large blue style from CSS
        if st.button("📸 TAKE PICTURE", key="show_cam_button"):
            st.session_state.show_camera = True
            # We need to reset camera_key here too to ensure camera refreshes
            # if user comes back to it without taking a picture previously
            st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}_show"
            st.rerun()

    # Condition: Show Camera Input after Big Button click
    else:
        # Use standard st.camera_input - no custom CSS applied here
        captured_image_buffer = st.camera_input(
            " ", # Label can be empty or minimal, often shown above preview
            key=st.session_state.camera_key,
            label_visibility="collapsed" # Hide the actual label text area
            )

        if captured_image_buffer is not None:
            st.session_state.photo_buffer = captured_image_buffer.getvalue()
            st.session_state.processing = True
            st.session_state.show_camera = False # Hide camera again for next round
            st.rerun()

# State 2: Processing photo (Unchanged)
elif st.session_state.processing:
    with st.spinner("Thinking..."):
        description, analysis_error = perform_image_analysis_simple(st.session_state.photo_buffer)
        st.session_state.photo_buffer = None # Clear buffer after use
        if analysis_error:
            st.session_state.error_message = analysis_error
            st.session_state.processing = False; st.session_state.show_play = False
            st.session_state.show_camera = False # Ensure we go back to big button on error
            st.rerun()
        else:
            audio_data, tts_error = text_to_speech_simple(description, DEFAULT_VOICE)
            if tts_error:
                st.session_state.error_message = tts_error
                st.session_state.processing = False; st.session_state.show_play = False
                st.session_state.show_camera = False # Ensure we go back to big button on error
                st.rerun()
            else:
                st.session_state.audio_data = audio_data
                st.session_state.processing = False; st.session_state.show_play = True
                # show_camera remains False, which is correct for showing results
                st.rerun()

# State 3: Show Play button (using HTML Component) and Audio (Unchanged logic, check component height)
elif st.session_state.show_play:
    if st.session_state.audio_data:
        audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
        audio_src = f"data:audio/mpeg;base64,{audio_base64}"

        # --- HTML Component (Same as before) ---
        component_html = f"""
        <style>
            .center-container {{ display: flex; flex-direction: column; align-items: center; width: 100%; }}
            #playButton {{
                background-color: #4CAF50; border: none; color: white;
                text-align: center; text-decoration: none; display: block; font-size: 40px;
                margin: 15px auto; cursor: pointer; border-radius: 12px;
                width: 70vw; height: 25vh; line-height: 25vh;
                box-sizing: border-box; padding: 0;
            }}
            #playButton:hover {{ color: white !important; background-color: #45a049; }}
            #audioPlayerContainer {{ text-align: center; margin-top: 15px; margin-bottom: 15px; width: 80%; }}
            #audioPlayer {{ width: 100%; }}
        </style>
        <div class="center-container" data-streamlit-component-button-audio>
             <div><button id="playButton">▶️ PLAY AUDIO</button></div>
             <div id="audioPlayerContainer"><audio id="audioPlayer" controls src="{audio_src}"></audio></div>
        </div>
        <script>
            const playButton = document.getElementById('playButton');
            const audioPlayer = document.getElementById('audioPlayer');
            let isBound = document.body.hasAttribute('data-button-bound');
            if (playButton && audioPlayer && !isBound) {{
                 playButton.addEventListener('click', function() {{
                     audioPlayer.play().catch(e => console.error("Audio play failed:", e));
                 }});
                 document.body.setAttribute('data-button-bound', 'true');
            }}
        </script>
        """
        # Adjust height if necessary based on Play button + audio player
        st.components.v1.html(component_html, height=350)

    else:
        st.error("Error: Audio data is missing.")

    # "Start Over" Button (uses general CSS for size, now secondary red style)
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        # Reset logic: Make sure to reset show_camera as well
        st.session_state.photo_buffer = None; st.session_state.processing = False
        st.session_state.audio_data = None; st.session_state.error_message = None
        st.session_state.show_play = False
        st.session_state.show_camera = False # <- Reset to show big button first
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}_reset" # Ensure camera refreshes
        st.rerun()

# Error Display Logic
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    # Make the Try Again button consistent (Red)
    if st.button("Try Again", type="secondary"): # Use secondary for red style
         st.session_state.error_message = None
         st.session_state.show_camera = False # <- Reset to show big button first
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}"
         st.rerun()
