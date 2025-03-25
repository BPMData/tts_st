# import streamlit as st
# import base64
# from image_backend import look_at_photo, encode_image_from_bytes
# import requests

# # Config
# st.set_page_config(page_title="Camera to Speech", layout="wide")
# LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
# LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# VOICE = "bella"
# TTS_MODEL = "tts-1"

# # Session state init
# if "mode" not in st.session_state:
#     st.session_state.mode = "camera"
# if "audio_data" not in st.session_state:
#     st.session_state.audio_data = None

# # TTS function
# def text_to_speech(text):
#     headers = {
#         "Authorization": f"Bearer {LEMONFOX_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "model": TTS_MODEL,
#         "input": text,
#         "voice": VOICE,
#         "response_format": "mp3"
#     }
#     response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
#     response.raise_for_status()
#     return response.content

# # Analyze image
# def analyze_image_and_generate_audio(image_bytes):
#     base64_image = encode_image_from_bytes(image_bytes)
#     description = look_at_photo(base64_image, upload=False)
#     if description:
#         return text_to_speech(description)
#     return None

# # Main flow
# if st.session_state.mode == "camera":
#     image = st.camera_input("Take a photo")
#     if image is not None:
#         st.session_state.audio_data = analyze_image_and_generate_audio(image.getvalue())
#         st.session_state.mode = "result"
#         st.rerun()

# elif st.session_state.mode == "result":
#     if st.session_state.audio_data:
#         st.audio(st.session_state.audio_data, format="audio/mp3")
#     if st.button("🔁 Start Over"):
#         st.session_state.mode = "camera"
#         st.session_state.audio_data = None
#         st.rerun()


# Gemini 2.5 Pro attempt

# import streamlit as st
# import requests
# import base64
# import time # To generate unique keys

# # Import functions from image_backend.py
# # Keep these backend calls and imports as requested
# try:
#     from image_backend import look_at_photo, encode_image_from_bytes
# except ImportError:
#     st.error("🚨 FATAL ERROR: image_backend.py not found. Cannot analyze images.")
#     # Define dummy functions if import fails to avoid NameErrors later
#     def encode_image_from_bytes(byte_data): return None
#     def look_at_photo(base64_image, upload=False): return "Error: image_backend.py not loaded."

# # --- Configuration ---
# st.set_page_config(
#     page_title="Simple Image-to-Speech",
#     page_icon="👁️‍🗨️",
#     layout="centered" # Centered might be simpler visually
# )

# # --- Constants ---
# LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# TTS_MODEL = "tts-1"
# DEFAULT_VOICE_KEY = "bella" # Hardcoded voice

# # --- API Keys Check ---
# # Fetch keys from secrets ONCE
# OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
# LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

# missing_keys = []
# if not OPENAI_API_KEY:
#     missing_keys.append("OpenAI (for image analysis)")
# if not LEMONFOX_API_KEY:
#     missing_keys.append("Lemonfox (for text-to-speech)")

# if missing_keys:
#     keys_str = " and ".join(missing_keys)
#     st.error(f"🚨 Error: Required API Key(s) missing in secrets: {keys_str}. App cannot function.")
#     # Stop execution if keys are missing
#     st.stop()

# # --- Helper Function: text_to_speech (Simplified & Hardcoded Voice) ---
# def text_to_speech(text):
#     """Converts text to speech using the Lemonfox API with the hardcoded Bella voice."""
#     if not LEMONFOX_API_KEY: # Should be caught above, but double-check
#         st.error("Cannot convert: Lemonfox API Key missing.")
#         return None
#     if not text:
#         st.warning("Cannot convert empty text description.")
#         return None

#     headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
#     # Use hardcoded voice DEFAULT_VOICE_KEY
#     data = {"model": TTS_MODEL, "input": text, "voice": DEFAULT_VOICE_KEY, "response_format": "mp3"}

#     try:
#         # Use a simple spinner
#         with st.spinner("🔊 Generating audio..."):
#             response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
#             response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
#         st.success("✅ Audio ready!")
#         return response.content
#     except requests.exceptions.RequestException as e:
#         st.error(f"Audio generation failed: {e}")
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during TTS: {e}")
#         return None

# # --- Helper Function: perform_image_analysis (Simplified Error Handling) ---
# def perform_image_analysis(image_bytes):
#     """Analyzes image using OpenAI and returns the description or None on error."""
#     if not OPENAI_API_KEY: # Should be caught above, but double-check
#          st.error("Cannot analyze: OpenAI API Key missing.")
#          return None
#     try:
#         with st.spinner("🖼️ Analyzing image..."):
#             base64_image = encode_image_from_bytes(image_bytes)
#             if base64_image is None: # Check if encoding failed
#                  st.error("Failed to encode image.")
#                  return None
#             # Assuming look_at_photo takes base64 string and upload flag (False for camera)
#             description = look_at_photo(base64_image, upload=False)

#         if description and "error" not in description.lower() and "fail" not in description.lower():
#             # st.success("✅ Image analyzed.") # Maybe too much visual clutter?
#             return description
#         else:
#             st.error(f"Image analysis failed: {description or 'No description returned.'}")
#             return None
#     except Exception as e:
#         st.error(f"Error during image analysis: {e}")
#         return None

# # --- Initialize Session State ---
# if 'view_state' not in st.session_state:
#     st.session_state.view_state = 'capture' # 'capture' or 'playback'
# if 'audio_data' not in st.session_state:
#     st.session_state.audio_data = None
# if 'camera_key' not in st.session_state:
#     st.session_state.camera_key = f"camera_{int(time.time())}" # Unique key to reset camera

# # --- Main App Logic ---

# # View 1: Capture Photo
# if st.session_state.view_state == 'capture':
#     # ONLY show the camera input
#     captured_image_buffer = st.camera_input(
#         "Take a picture to describe",
#         key=st.session_state.camera_key,
#         help="Point the camera and click the button to take a photo."
#     )

#     # If a photo was just taken
#     if captured_image_buffer is not None:
#         st.session_state.audio_data = None # Clear previous audio if any

#         # 1. Analyze the image
#         image_bytes = captured_image_buffer.getvalue()
#         description = perform_image_analysis(image_bytes)

#         if description:
#             # 2. Convert description to speech (using hardcoded voice)
#             audio_bytes = text_to_speech(description)

#             if audio_bytes:
#                 # 3. Store audio and switch view
#                 st.session_state.audio_data = audio_bytes
#                 st.session_state.view_state = 'playback'
#                 # Use rerun to immediately switch the view
#                 st.rerun()
#             else:
#                 # TTS failed, stay in capture view, error already shown by text_to_speech
#                 pass
#         else:
#             # Analysis failed, stay in capture view, error already shown by perform_image_analysis
#             pass

# # View 2: Playback Audio
# elif st.session_state.view_state == 'playback':

#     # Ensure audio data exists before showing player
#     if st.session_state.audio_data:
#         st.audio(st.session_state.audio_data, format="audio/mp3", start_time=0)
#     else:
#         # Should not happen if logic is correct, but good failsafe
#         st.error("Error: Audio data not found.")

#     # Start Over Button
#     if st.button("Start Over", key="start_over_button"):
#         # Reset state variables
#         st.session_state.view_state = 'capture'
#         st.session_state.audio_data = None
#         # Generate a new key for the camera to force reset
#         st.session_state.camera_key = f"camera_{int(time.time())}"
#         # Rerun to switch back to the capture view
#         st.rerun()

# # --- Footer (Optional, but good for context) ---
# st.markdown("---")
# st.caption("Simple Image-to-Speech")

# CGPT 4.o attempt for BIG BUTTONS

import streamlit as st
import requests
import base64
from image_backend import look_at_photo, encode_image_from_bytes

# --- Config & Keys ---
st.set_page_config(page_title="Camera to Speech", layout="wide")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
VOICE = "bella"
TTS_MODEL = "tts-1"

# --- Enlarge Buttons via Custom CSS ---
st.markdown("""
    <style>
        /* Make camera button big */
        div[data-testid="stCameraInput"] button {
            background-color: #1976D2;
            color: white;
            font-size: 36px;
            padding: 30px 40px;
            border-radius: 16px;
            width: 80vw;
            height: 15vh;
        }

        /* General Streamlit button (Start Over) */
        div[data-testid="stButton"] button {
            background-color: #d32f2f;
            color: white;
            font-size: 36px;
            padding: 30px;
            width: 80vw;
            height: 15vh;
            border-radius: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# --- TTS Function ---
def text_to_speech(text):
    headers = {
        "Authorization": f"Bearer {LEMONFOX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": TTS_MODEL,
        "input": text,
        "voice": VOICE,
        "response_format": "mp3"
    }
    response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    return response.content

# --- State Init ---
if "mode" not in st.session_state:
    st.session_state.mode = "camera"
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# --- Main Flow ---
if st.session_state.mode == "camera":
    image = st.camera_input("Take a Picture")
    if image is not None:
        base64_image = encode_image_from_bytes(image.getvalue())
        description = look_at_photo(base64_image, upload=False)
        audio = text_to_speech(description)
        st.session_state.audio_data = audio
        st.session_state.mode = "result"
        st.rerun()

elif st.session_state.mode == "result":
    if st.session_state.audio_data:
        audio_b64 = base64.b64encode(st.session_state.audio_data).decode("utf-8")
        st.components.v1.html(f"""
            <div style="display: flex; flex-direction: column; align-items: center;">
                <button id="playAudio" style="
                    background-color: #4CAF50;
                    color: white;
                    font-size: 40px;
                    width: 80vw;
                    height: 15vh;
                    border: none;
                    border-radius: 16px;
                    margin-bottom: 30px;
                ">▶️ PLAY AUDIO</button>

                <audio id="player" src="data:audio/mp3;base64,{audio_b64}" controls style="display:none;"></audio>

                <script>
                    const btn = document.getElementById("playAudio");
                    const player = document.getElementById("player");
                    btn.addEventListener("click", () => {{
                        player.play();
                    }});
                </script>
            </div>
        """, height=300)

    if st.button("🔄 START OVER"):
        st.session_state.mode = "camera"
        st.session_state.audio_data = None
        st.rerun()

