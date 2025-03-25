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

if not OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY")
if not LEMONFOX_API_KEY: missing_keys.append("LEMONFOX_API_KEY")

# --- Custom CSS Injection (Final Version) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp { padding: 1rem; }

            /* Make Camera Input Button Huge */
            div[data-testid="stCameraInput"] > div > button {
                background-color: #008CBA; /* Blue */
                border: none; color: white; padding: 50px 50px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 48px; margin: 20px 2px; cursor: pointer;
                border-radius: 12px; width: 80vw; height: 50vh; line-height: 1.2;
                position: relative; /* Ensure it's layerable */
                z-index: 10; /* Keep button on top */
                box-sizing: border-box;
            }
            /* Camera Button Hover */
            div[data-testid="stCameraInput"] > div > button:hover {
                 color: white !important; /* Keep text white */
                 opacity: 0.9;
            }
            /* Hide the text label above camera button */
            div[data-testid="stCameraInput"] label { display: none; }

            /* Hide the live video preview within camera input */
            div[data-testid="stCameraInput"] video {
                display: none !important; /* Force hide the video element */
            }

            /* General Style for Streamlit Action Buttons (Start Over / Try Again) */
            div[data-testid="stButton"] > button {
                border: none; color: white; padding: 40px 40px;
                text-align: center; text-decoration: none; display: inline-block;
                font-size: 40px; margin: 15px 2px; cursor: pointer;
                border-radius: 12px; width: 70vw; /* Keep width consistent */
                min-height: 15vh; /* Use min-height for flexibility */
                line-height: 1.2; box-sizing: border-box;
                display: flex !important; align-items: center !important; justify-content: center !important;
            }
            /* HOVER state for standard Streamlit buttons */
            div[data-testid="stButton"] > button:hover {
                 color: white !important; /* Keep text white */
                 opacity: 0.9;
            }
            /* Specific style for Start Over button (Red) */
             div[data-testid="stButton"] > button[kind="secondary"] {
                 background-color: #f44336; /* Red */
                 min-height: 25vh; /* Make Start Over taller like Play */
                 height: 25vh; /* Explicit height can also work */
             }
             /* Hover for secondary/Red button */
             div[data-testid="stButton"] > button[kind="secondary"]:hover {
                 background-color: #d32f2f; /* Darker Red */
                 color: white !important; opacity: 1.0;
             }
             /* Style for Try Again button (default green if not secondary) */
              div[data-testid="stButton"] > button:not([kind="secondary"]) {
                  background-color: #4CAF50; /* Green */
              }
              div[data-testid="stButton"] > button:not([kind="secondary"]):hover {
                  background-color: #45a049; /* Darker Green */
              }


             /* Centering containers */
             .stApp > div:first-child {
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: 95vh;
             }
             /* Target containers holding our main elements for centering */
             div[data-testid="stVerticalBlock"],
             div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
             div[data-streamlit-component-button-audio] { /* Target our component wrapper */
                 align-items: center !important; display: flex !important;
                 flex-direction: column !important; justify-content: center !important;
                 width: 100% !important;
             }
             /* Add consistent gap AFTER the HTML component */
             div[data-streamlit-component-button-audio] {
                  margin-bottom: 20px; /* Add space below the component */
             }
             /* Remove extra margin potentially added by Streamlit around buttons */
              div[data-testid="stButton"] {
                  margin-bottom: 10px; /* Reduce bottom margin */
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
if "photo_buffer" not in st.session_state: st.session_state.photo_buffer = None
if "processing" not in st.session_state: st.session_state.processing = False
if "audio_data" not in st.session_state: st.session_state.audio_data = None
if "error_message" not in st.session_state: st.session_state.error_message = None
if "show_play" not in st.session_state: st.session_state.show_play = False
if "camera_key" not in st.session_state: st.session_state.camera_key = "cam_initial" # Key for resetting camera

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

# State 3: Show Play button (using HTML Component) and Audio
elif st.session_state.show_play:
    if st.session_state.audio_data:
        # 1. Encode audio data to base64
        audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
        audio_src = f"data:audio/mpeg;base64,{audio_base64}"

        # 2. Define HTML/CSS/JS for the component
        component_html = f"""
        <style>
            /* Container for centering */
            .center-container {{
                display: flex; flex-direction: column; align-items: center; width: 100%;
            }}
            /* Style for the custom play button */
            #playButton {{
                background-color: #4CAF50; /* Green */
                border: none; color: white;
                text-align: center; text-decoration: none; display: block;
                font-size: 40px; margin: 15px auto; cursor: pointer; border-radius: 12px;
                width: 70vw; /* Width like other buttons */
                height: 25vh; /* Height like start over button */
                line-height: 25vh; /* Vertically center text */
                box-sizing: border-box; padding: 0;
            }}
            #playButton:hover {{ color: white !important; background-color: #45a049; }}
            /* Container for audio player */
             #audioPlayerContainer {{
                 text-align: center;
                 margin-top: 15px; /* Space below play button */
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
            let isBound = document.body.hasAttribute('data-button-bound');

            if (playButton && audioPlayer && !isBound) {{
                playButton.addEventListener('click', function() {{
                    console.log("Play button clicked!");
                    audioPlayer.play().catch(e => console.error("Audio play failed:", e));
                }});
                document.body.setAttribute('data-button-bound', 'true');
                console.log("Event listener bound.");
            }} else if (isBound) {{
                 console.log("Event listener already bound.");
            }} else {{
                console.error("Component elements not found for binding!");
            }}
        </script>
        """

        # 3. Render the component with adjusted height
        # Height should accommodate button (~25vh) + player (~50px) + margins (~30px)
        # Let's estimate around 350px total should be safe
        st.components.v1.html(component_html, height=350) # Adjust if gap reappears/content cut off

    else:
        st.error("Error: Audio data is missing.") # Fallback

    # Keep the standard Streamlit button for "Start Over" (styled large by CSS)
    if st.button("🔄 START OVER", key="reset", type="secondary"):
        # Reset state variables to initial values
        st.session_state.photo_buffer = None; st.session_state.processing = False
        st.session_state.audio_data = None; st.session_state.error_message = None
        st.session_state.show_play = False
        # Important: Change camera key to force reset
        st.session_state.camera_key = f"cam_{hash(st.session_state.camera_key)}"
        st.rerun()

# Display errors if they occurred in processing
if st.session_state.error_message and not st.session_state.processing:
    st.error(st.session_state.error_message)
    # Add a button to acknowledge error and reset
    if st.button("Try Again"): # Uses general button style (should be green)
         st.session_state.error_message = None
         st.session_state.camera_key = f"cam_err_{hash(st.session_state.camera_key)}" # Reset camera on error ack
         st.rerun()
