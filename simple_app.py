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
# CHANGES MADE HERE: Modified Camera Input CSS, Added Preview Size CSS
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp { padding: 1rem; }

            /* --- MODIFIED: Make Camera Input Button Prominent but NOT Huge --- */
            div[data-testid="stCameraInput"] > div > button {
                background-color: #008CBA; border: none; color: white; padding: 20px 30px; /* Reduced padding */
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 24px; /* Reduced font size */ margin: 20px 2px; cursor: pointer;
                border-radius: 12px;
                width: auto; /* Let button size naturally */
                height: auto; /* Let button size naturally */
                /* Removed fixed width/height and large line-height */
            }
            div[data-testid="stCameraInput"] > div > button:hover { color: white !important; opacity: 0.9; }
            /* Keep label hidden if you don't want Streamlit's default label */
            /* div[data-testid="stCameraInput"] label { display: none; } */


            /* --- NEW: Make Camera Input PREVIEW smaller --- */
            /* Target the container that often holds the video/preview */
            div[data-testid="stCameraInput"] > div > div {
                max-width: 450px !important; /* Adjust max width as needed */
                margin: 10px auto !important; /* Center the preview container */
                overflow: hidden; /* Hide overflow if necessary */
            }
             /* Target the video element directly for finer control */
            div[data-testid="stCameraInput"] video {
                 max-height: 300px !important; /* Adjust max height */
                 width: 100% !important; /* Make video fill its container width */
                 height: auto !important; /* Maintain aspect ratio */
                 display: block !important;
                 margin: 0 auto !important;
            }


            /* General Style for Streamlit Action Buttons (Start Over / Try Again) - Unchanged */
            div[data-testid="stButton"] > button {
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
            div[data-testid="stButton"] > button:hover { color: white !important; opacity: 0.9; }
            div[data-testid="stButton"] > button[kind="secondary"] { background-color: #f44336; /* Red */ }
            div[data-testid="stButton"] > button[kind="secondary"]:hover { background-color: #d32f2f; color: white !important; opacity: 1.0; }

             /* Centering - Unchanged */
             .stApp > div:first-child {
                 display: flex; flex-direction: column; align-items: center;
                 justify-content: center; min-height: 95vh;
             }
             /* Target containers for centering content - Unchanged */
             div[data-testid="stVerticalBlock"],
             div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
             div[data-streamlit-component-button-audio] { /* Target our component wrapper */
                  align-items: center !important;
                  display: flex !important;
                  flex-direction: column !important;
                  justify-content: center !important;
                  width: 100% !important; /* Ensure component takes space */
             }
             /* Add some gap AFTER the component IF NEEDED - Unchanged */
             div[data-streamlit-component-button-audio] + div[data-testid="element-container"] {
                   margin-top: 20px; /* Space before the Start Over button */
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
    # Changed the label slightly - CSS still hides the default label display location though.
    # The button itself will likely show a camera icon or default text.
    captured_image_buffer = st.camera_input(
        "Take Picture", key=st.session_state.camera_key #, label_visibility="hidden" # You can optionally keep this hidden
        )
    if captured_image_buffer is not None:
        st.session_state.photo_buffer = captured_image_buffer.getvalue()
        st.session_state.processing = True
        st.rerun()

# State 2: Processing photo
elif st.session_state.processing:
    with st.spinner("Thinking..."):
        description, analysis_error = perform_image_analysis_simple(st.session_state.photo_buffer)
        st.session_state.photo_buffer = None # Clear buffer after use
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

# State 3: Show Play button (using HTML Component) and Audio
elif st.session_state.show_play:
    if st.session_state.audio_data:
        audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
        audio_src = f"data:audio/mpeg;base64,{audio_base64}"

        # --- HTML Component (Unchanged from your original, should work fine) ---
        component_html = f"""
        <style>
            .center-container {{
                display: flex; flex-direction: column; align-items: center; width: 100%;
            }}
            /* Style for the custom play button - MAKE IT BIG AGAIN */
            #playButton {{
                background-color: #4CAF50; /* Green */
                border: none; color: white;
                text-align: center; text-decoration: none; display: block;
                font-size: 40px; /* Large font */
                margin: 15px auto; cursor: pointer; border-radius: 12px;
                width: 70vw; /* Set desired width */
                height: 25vh; /* Set desired height */
                line-height: 25vh; /* Vertically center text (matches height) */
                box-sizing: border-box;
                padding: 0; /* Remove padding if line-height centers */
            }}
            #playButton:hover {{ color: white !important; background-color: #45a049; }}

            #audioPlayerContainer {{
                 text-align: center;
                 margin-top: 15px; /* Slightly reduced margin */
                 margin-bottom: 15px; /* Add margin below player */
                 width: 80%;
             }}
             #audioPlayer {{ width: 100%; }}
        </style>

        <div class="center-container" data-streamlit-component-button-audio>
             <div><button id="playButton">▶️ PLAY AUDIO</button></div>
             <div id="audioPlayerContainer"><audio id="audioPlayer" controls src="{audio_src}"></audio></div>
        </div>

        <script>
            const playButton = document.getElementById('playButton');
            const audioPlayer = document.getElementById('audioPlayer');
            let isBound = document.body.hasAttribute('data-button-bound'); // Check if already bound

            if (playButton && audioPlayer && !isBound) {{
                 playButton.addEventListener('click', function() {{
                     console.log("Play button clicked!");
                     audioPlayer.play().catch(e => console.error("Audio play failed:", e));
                 }});
                 document.body.setAttribute('data-button-bound', 'true'); // Mark as bound
                 console.log("Event listener bound.");
            }} else if (isBound) {{
                 console.log("Event listener already bound.");
            }} else {{
                 console.error("Component elements not found for binding!");
            }}
        </script>
        """
        # --- RENDER COMPONENT ---
        # You might still need to adjust this height based on the content.
        # The button is 25vh, player is maybe 50px, plus margins.
        # Let's try estimating based on vh (e.g., 25vh might be ~200-250px depending on screen) + player + margins
        st.components.v1.html(component_html, height=350) # Adjusted height slightly

    else:
        st.error("Error: Audio data is missing.")

    # "Start Over" Button (uses general CSS for size - Unchanged)
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        # Reset logic remains the same...
        st.session_state.photo_buffer = None; st.session_state.processing = False
        st.session_state.audio_data = None; st.session_state.error_message = None
        st.session_state.show_play = False
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}"
        st.rerun()

# Error Display Logic (unchanged)
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    # Make the Try Again button consistent with Start Over if desired
    if st.button("Try Again"): # Consider adding type="secondary" or custom class if needed
         st.session_state.error_message = None
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}"
         st.rerun()
