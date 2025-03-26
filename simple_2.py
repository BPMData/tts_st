# # import streamlit as st
# # import base64
# # from image_backend import look_at_photo, encode_image_from_bytes
# # import requests

# # # Config
# # st.set_page_config(page_title="Camera to Speech", layout="wide")
# # LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
# # LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# # VOICE = "bella"
# # TTS_MODEL = "tts-1"

# # # Session state init
# # if "mode" not in st.session_state:
# #     st.session_state.mode = "camera"
# # if "audio_data" not in st.session_state:
# #     st.session_state.audio_data = None

# # # TTS function
# # def text_to_speech(text):
# #     headers = {
# #         "Authorization": f"Bearer {LEMONFOX_API_KEY}",
# #         "Content-Type": "application/json"
# #     }
# #     data = {
# #         "model": TTS_MODEL,
# #         "input": text,
# #         "voice": VOICE,
# #         "response_format": "mp3"
# #     }
# #     response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
# #     response.raise_for_status()
# #     return response.content

# # # Analyze image
# # def analyze_image_and_generate_audio(image_bytes):
# #     base64_image = encode_image_from_bytes(image_bytes)
# #     description = look_at_photo(base64_image, upload=False)
# #     if description:
# #         return text_to_speech(description)
# #     return None

# # # Main flow
# # if st.session_state.mode == "camera":
# #     image = st.camera_input("Take a photo")
# #     if image is not None:
# #         st.session_state.audio_data = analyze_image_and_generate_audio(image.getvalue())
# #         st.session_state.mode = "result"
# #         st.rerun()

# # elif st.session_state.mode == "result":
# #     if st.session_state.audio_data:
# #         st.audio(st.session_state.audio_data, format="audio/mp3")
# #     if st.button("🔁 Start Over"):
# #         st.session_state.mode = "camera"
# #         st.session_state.audio_data = None
# #         st.rerun()


# # Gemini 2.5 Pro attempt

# # import streamlit as st
# # import requests
# # import base64
# # import time # To generate unique keys

# # # Import functions from image_backend.py
# # # Keep these backend calls and imports as requested
# # try:
# #     from image_backend import look_at_photo, encode_image_from_bytes
# # except ImportError:
# #     st.error("🚨 FATAL ERROR: image_backend.py not found. Cannot analyze images.")
# #     # Define dummy functions if import fails to avoid NameErrors later
# #     def encode_image_from_bytes(byte_data): return None
# #     def look_at_photo(base64_image, upload=False): return "Error: image_backend.py not loaded."

# # # --- Configuration ---
# # st.set_page_config(
# #     page_title="Simple Image-to-Speech",
# #     page_icon="👁️‍🗨️",
# #     layout="centered" # Centered might be simpler visually
# # )

# # # --- Constants ---
# # LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# # TTS_MODEL = "tts-1"
# # DEFAULT_VOICE_KEY = "bella" # Hardcoded voice

# # # --- API Keys Check ---
# # # Fetch keys from secrets ONCE
# # OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
# # LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")

# # missing_keys = []
# # if not OPENAI_API_KEY:
# #     missing_keys.append("OpenAI (for image analysis)")
# # if not LEMONFOX_API_KEY:
# #     missing_keys.append("Lemonfox (for text-to-speech)")

# # if missing_keys:
# #     keys_str = " and ".join(missing_keys)
# #     st.error(f"🚨 Error: Required API Key(s) missing in secrets: {keys_str}. App cannot function.")
# #     # Stop execution if keys are missing
# #     st.stop()

# # # --- Helper Function: text_to_speech (Simplified & Hardcoded Voice) ---
# # def text_to_speech(text):
# #     """Converts text to speech using the Lemonfox API with the hardcoded Bella voice."""
# #     if not LEMONFOX_API_KEY: # Should be caught above, but double-check
# #         st.error("Cannot convert: Lemonfox API Key missing.")
# #         return None
# #     if not text:
# #         st.warning("Cannot convert empty text description.")
# #         return None

# #     headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
# #     # Use hardcoded voice DEFAULT_VOICE_KEY
# #     data = {"model": TTS_MODEL, "input": text, "voice": DEFAULT_VOICE_KEY, "response_format": "mp3"}

# #     try:
# #         # Use a simple spinner
# #         with st.spinner("🔊 Generating audio..."):
# #             response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
# #             response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
# #         st.success("✅ Audio ready!")
# #         return response.content
# #     except requests.exceptions.RequestException as e:
# #         st.error(f"Audio generation failed: {e}")
# #         return None
# #     except Exception as e:
# #         st.error(f"An unexpected error occurred during TTS: {e}")
# #         return None

# # # --- Helper Function: perform_image_analysis (Simplified Error Handling) ---
# # def perform_image_analysis(image_bytes):
# #     """Analyzes image using OpenAI and returns the description or None on error."""
# #     if not OPENAI_API_KEY: # Should be caught above, but double-check
# #          st.error("Cannot analyze: OpenAI API Key missing.")
# #          return None
# #     try:
# #         with st.spinner("🖼️ Analyzing image..."):
# #             base64_image = encode_image_from_bytes(image_bytes)
# #             if base64_image is None: # Check if encoding failed
# #                  st.error("Failed to encode image.")
# #                  return None
# #             # Assuming look_at_photo takes base64 string and upload flag (False for camera)
# #             description = look_at_photo(base64_image, upload=False)

# #         if description and "error" not in description.lower() and "fail" not in description.lower():
# #             # st.success("✅ Image analyzed.") # Maybe too much visual clutter?
# #             return description
# #         else:
# #             st.error(f"Image analysis failed: {description or 'No description returned.'}")
# #             return None
# #     except Exception as e:
# #         st.error(f"Error during image analysis: {e}")
# #         return None

# # # --- Initialize Session State ---
# # if 'view_state' not in st.session_state:
# #     st.session_state.view_state = 'capture' # 'capture' or 'playback'
# # if 'audio_data' not in st.session_state:
# #     st.session_state.audio_data = None
# # if 'camera_key' not in st.session_state:
# #     st.session_state.camera_key = f"camera_{int(time.time())}" # Unique key to reset camera

# # # --- Main App Logic ---

# # # View 1: Capture Photo
# # if st.session_state.view_state == 'capture':
# #     # ONLY show the camera input
# #     captured_image_buffer = st.camera_input(
# #         "Take a picture to describe",
# #         key=st.session_state.camera_key,
# #         help="Point the camera and click the button to take a photo."
# #     )

# #     # If a photo was just taken
# #     if captured_image_buffer is not None:
# #         st.session_state.audio_data = None # Clear previous audio if any

# #         # 1. Analyze the image
# #         image_bytes = captured_image_buffer.getvalue()
# #         description = perform_image_analysis(image_bytes)

# #         if description:
# #             # 2. Convert description to speech (using hardcoded voice)
# #             audio_bytes = text_to_speech(description)

# #             if audio_bytes:
# #                 # 3. Store audio and switch view
# #                 st.session_state.audio_data = audio_bytes
# #                 st.session_state.view_state = 'playback'
# #                 # Use rerun to immediately switch the view
# #                 st.rerun()
# #             else:
# #                 # TTS failed, stay in capture view, error already shown by text_to_speech
# #                 pass
# #         else:
# #             # Analysis failed, stay in capture view, error already shown by perform_image_analysis
# #             pass

# # # View 2: Playback Audio
# # elif st.session_state.view_state == 'playback':

# #     # Ensure audio data exists before showing player
# #     if st.session_state.audio_data:
# #         st.audio(st.session_state.audio_data, format="audio/mp3", start_time=0)
# #     else:
# #         # Should not happen if logic is correct, but good failsafe
# #         st.error("Error: Audio data not found.")

# #     # Start Over Button
# #     if st.button("Start Over", key="start_over_button"):
# #         # Reset state variables
# #         st.session_state.view_state = 'capture'
# #         st.session_state.audio_data = None
# #         # Generate a new key for the camera to force reset
# #         st.session_state.camera_key = f"camera_{int(time.time())}"
# #         # Rerun to switch back to the capture view
# #         st.rerun()

# # # --- Footer (Optional, but good for context) ---
# # st.markdown("---")
# # st.caption("Simple Image-to-Speech")

# ########################################## CGPT 4.o attempt for BIG BUTTONS

# import streamlit as st
# import requests
# import base64
# from image_backend import look_at_photo, encode_image_from_bytes

# # --- Config ---
# st.set_page_config(page_title="Camera to Speech", layout="wide")
# LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
# LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# VOICE = "bella"
# TTS_MODEL = "tts-1"

# # --- Enlarge Buttons ---
# st.markdown("""
#     <style>
#         div[data-testid="stCameraInput"] button {
#             background-color: #1976D2;
#             color: white;
#             font-size: 36px;
#             padding: 30px 40px;
#             border-radius: 16px;
#             width: 80vw;
#             height: 15vh;
#         }

#         div[data-testid="stButton"] button {
#             background-color: #d32f2f;
#             color: white;
#             font-size: 36px;
#             padding: 30px;
#             width: 80vw;
#             height: 15vh;
#             border-radius: 16px;
#         }
#     </style>
# """, unsafe_allow_html=True)

# # --- TTS ---
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

# # --- State Init ---
# if "mode" not in st.session_state:
#     st.session_state.mode = "camera"
# if "audio_data" not in st.session_state:
#     st.session_state.audio_data = None

# # --- App Logic ---
# if st.session_state.mode == "camera":
#     image = st.camera_input("Take a Picture")
#     if image is not None:
#         with st.spinner("Analyzing image and generating audio..."):
#             base64_image = encode_image_from_bytes(image.getvalue())
#             description = look_at_photo(base64_image, upload=False)
#             audio = text_to_speech(description)
#             st.session_state.audio_data = audio
#             st.session_state.mode = "result"
#             st.rerun()

# elif st.session_state.mode == "result":
#     if st.session_state.audio_data:
#         audio_b64 = base64.b64encode(st.session_state.audio_data).decode("utf-8")
#         st.components.v1.html(f"""
#             <div style="display: flex; flex-direction: column; align-items: center;">
#                 <button id="playAudio" style="
#                     background-color: #4CAF50;
#                     color: white;
#                     font-size: 40px;
#                     width: 80vw;
#                     height: 15vh;
#                     border: none;
#                     border-radius: 16px;
#                     margin-bottom: 30px;
#                 ">▶️ PLAY AUDIO</button>

#                 <audio id="player" src="data:audio/mp3;base64,{audio_b64}" controls style="display:none;"></audio>

#                 <script>
#                     const btn = document.getElementById("playAudio");
#                     const player = document.getElementById("player");
#                     btn.addEventListener("click", () => {{
#                         player.play();
#                     }});
#                 </script>
#             </div>
#         """, height=300)

#     if st.button("🔄 START OVER"):
#         st.session_state.mode = "camera"
#         st.session_state.audio_data = None
#         st.rerun()


# ################### Gemini 2.5 Pro for BIG BUTTON

# # import streamlit as st
# # import requests
# # import base64
# # import io
# # import time # Used for unique keys

# # # --- Try importing backend functions ---
# # try:
# #     # Make sure image_backend.py is in the same directory
# #     from image_backend import look_at_photo, encode_image_from_bytes
# #     BACKEND_LOADED = True
# # except ImportError:
# #     st.error("FATAL ERROR: image_backend.py not found in the project directory.")
# #     # Define dummy functions if import fails to prevent NameErrors
# #     def encode_image_from_bytes(byte_data): return None
# #     def look_at_photo(base64_image, upload=False): return "Error: Backend not loaded."
# #     BACKEND_LOADED = False

# # # --- Configuration & Constants ---
# # st.set_page_config(layout="wide") # Use wide layout to give buttons space
# # LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
# # TTS_MODEL = "tts-1"
# # DEFAULT_VOICE = "bella" # Using Bella as requested previously
# # MAX_CHAR_LIMIT = 4000

# # # --- API Keys Check ---
# # missing_keys = []
# # OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
# # LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
# # if not OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY (for image analysis)")
# # if not LEMONFOX_API_KEY: missing_keys.append("LEMONFOX_API_KEY (for text-to-speech)")

# # # --- Custom CSS Injection for LARGE Buttons and Centering ---
# # large_button_css = """
# # <style>
# #     /* Hide default Streamlit UI elements */
# #     #MainMenu {visibility: hidden;}
# #     header {visibility: hidden;}
# #     footer {visibility: hidden;}
# #     .stApp { padding: 0.5rem; } /* Reduce padding to maximize space */

# #     /* Center the main content block vertically and horizontally */
# #     .stApp > div:first-child {
# #         display: flex;
# #         flex-direction: column;
# #         align-items: center;
# #         justify-content: center;
# #         min-height: 98vh; /* Use almost full viewport height */
# #         width: 100%;
# #     }

# #     /* Ensure block containers fill width and center content */
# #     div[data-testid="stVerticalBlock"],
# #     div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
# #     div[data-testid="stCameraInput"], /* Target camera container */
# #     div[data-streamlit-component-button-audio] /* Target our custom component wrapper */
# #     {
# #         display: flex !important;
# #         flex-direction: column !important;
# #         align-items: center !important;
# #         justify-content: center !important;
# #         width: 90% !important; /* Use significant width */
# #         max-width: 700px; /* Add a max-width for very large screens */
# #         margin: 10px auto !important; /* Center blocks horizontally */
# #     }

# #     /* --- Style the Camera Input Button --- */
# #     div[data-testid="stCameraInput"] > div > button {
# #         background-color: #008CBA; /* Blue */
# #         border: none;
# #         color: white;
# #         padding: 30px 0px; /* Generous vertical padding, zero horizontal */
# #         text-align: center;
# #         text-decoration: none;
# #         display: flex !important; /* Use flex to center icon/text */
# #         align-items: center !important;
# #         justify-content: center !important;
# #         font-size: 35px; /* Large font */
# #         margin: 15px 0px; /* Margin top/bottom */
# #         cursor: pointer;
# #         border-radius: 15px;
# #         width: 100%; /* Make button fill container width */
# #         min-height: 20vh; /* Significant minimum height */
# #         box-sizing: border-box;
# #         line-height: 1.2; /* Adjust line height for text wrapping */
# #     }
# #     div[data-testid="stCameraInput"] > div > button:hover {
# #         color: white !important;
# #         opacity: 0.9;
# #     }
# #     /* Optional: Hide the default label above the camera button */
# #     div[data-testid="stCameraInput"] label {
# #          display: none;
# #     }

# #     /* --- Keep Camera Preview Relatively Small --- */
# #     div[data-testid="stCameraInput"] > div > div {
# #         max-width: 350px !important; /* Smaller preview width */
# #         margin: 5px auto !important;
# #         overflow: hidden;
# #     }
# #     div[data-testid="stCameraInput"] video {
# #          max-height: 250px !important; /* Smaller preview height */
# #          width: 100% !important;
# #          height: auto !important;
# #          display: block !important;
# #          margin: 0 auto !important;
# #     }

# #     /* --- Style for Standard Streamlit Buttons (Start Over / Try Again) --- */
# #     div[data-testid="stButton"] > button {
# #         border: none;
# #         color: white;
# #         padding: 30px 0px; /* Generous vertical padding */
# #         text-align: center;
# #         text-decoration: none;
# #         display: flex !important; /* Use flex to center text */
# #         align-items: center !important;
# #         justify-content: center !important;
# #         font-size: 35px; /* Large font */
# #         margin: 15px 0px; /* Margin top/bottom */
# #         cursor: pointer;
# #         border-radius: 15px;
# #         width: 100%; /* Make button fill container width */
# #         min-height: 20vh; /* Significant minimum height */
# #         box-sizing: border-box;
# #         line-height: 1.2; /* Adjust line height */
# #     }
# #     div[data-testid="stButton"] > button:hover {
# #         color: white !important;
# #         opacity: 0.9;
# #     }
# #     /* Specific color for the 'secondary' type button (like Start Over) */
# #     div[data-testid="stButton"] > button[kind="secondary"] {
# #         background-color: #f44336; /* Red */
# #     }
# #     div[data-testid="stButton"] > button[kind="secondary"]:hover {
# #         background-color: #d32f2f; /* Darker red */
# #         color: white !important;
# #         opacity: 1.0;
# #     }

# #     /* --- Style for Custom HTML Play Button --- */
# #     /* Container for the custom component */
# #     .center-container {
# #         display: flex;
# #         flex-direction: column;
# #         align-items: center;
# #         width: 100%; /* Fill the stVerticalBlock container */
# #     }
# #     /* The custom play button itself */
# #     #playButton {
# #         background-color: #4CAF50; /* Green */
# #         border: none;
# #         color: white;
# #         text-align: center;
# #         text-decoration: none;
# #         display: flex !important; /* Use flex to center text */
# #         align-items: center !important;
# #         justify-content: center !important;
# #         font-size: 35px; /* Large font */
# #         margin: 15px 0; /* Consistent margin */
# #         cursor: pointer;
# #         border-radius: 15px;
# #         width: 100%; /* Fill container width */
# #         height: 25vh; /* Make it tall */
# #         box-sizing: border-box;
# #         padding: 0; /* Remove padding if flex centers */
# #         line-height: 1.2; /* Allow text wrapping */
# #     }
# #     #playButton:hover {
# #         color: white !important;
# #         background-color: #45a049; /* Darker green */
# #     }
# #     /* Container for the standard HTML audio player */
# #     #audioPlayerContainer {
# #          text-align: center;
# #          margin-top: 10px; /* Space above player */
# #          margin-bottom: 10px; /* Space below player */
# #          width: 100%; /* Full width */
# #      }
# #      #audioPlayer {
# #          width: 100%; /* Make player fill its container */
# #      }

# # </style>
# # """
# # st.markdown(large_button_css, unsafe_allow_html=True)

# # # --- Helper Functions (TTS and Analysis - slightly simplified) ---
# # def text_to_speech_simple(text, voice_key):
# #     # API key check done globally, no need to repeat here unless Lemonfox key is optional
# #     if not text: return None, "No text description found to speak."
# #     if len(text) > MAX_CHAR_LIMIT: return None, f"Text too long ({len(text)} > {MAX_CHAR_LIMIT}). Please try a simpler image."

# #     headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
# #     data = {"model": TTS_MODEL, "input": text, "voice": voice_key, "response_format": "mp3"}
# #     try:
# #         response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=45)
# #         response.raise_for_status() # Checks for HTTP errors (4xx, 5xx)
# #         return response.content, None # Success
# #     except requests.exceptions.Timeout:
# #         return None, "Audio generation timed out. Please try again."
# #     except requests.exceptions.RequestException as e:
# #         # Try to provide a more specific error if possible
# #         err_msg = f"Audio generation failed: {e}"
# #         if e.response is not None:
# #             try:
# #                 err_details = e.response.json()
# #                 err_msg += f" (Details: {err_details.get('detail', e.response.text)})"
# #             except requests.exceptions.JSONDecodeError:
# #                 err_msg += f" (Status: {e.response.status_code})"
# #         return None, err_msg
# #     except Exception as e: # Catch any other unexpected errors
# #         return None, f"An unexpected error occurred during audio generation: {e}"

# # def perform_image_analysis_simple(image_bytes):
# #     # API key check done globally
# #     if not image_bytes: return None, "No image data captured."
# #     try:
# #         base64_image = encode_image_from_bytes(image_bytes) # From image_backend.py
# #         if not base64_image: return None, "Failed to process image data."

# #         description = look_at_photo(base64_image, upload=False) # From image_backend.py

# #         # Check for valid description (basic check)
# #         if description and isinstance(description, str) and "error" not in description.lower() and "fail" not in description.lower() and len(description) > 5:
# #             return description.strip(), None # Success, strip whitespace
# #         elif not description:
# #              return None, "Image analysis returned no description."
# #         else:
# #              # Attempt to return the specific error if backend provided one
# #              return None, f"Image analysis failed: {description}"

# #     except Exception as e: # Catch errors during the backend call
# #         return None, f"An error occurred during image analysis: {e}"

# # # --- Initialize Session State ---
# # if "photo_buffer" not in st.session_state: st.session_state.photo_buffer = None
# # if "processing" not in st.session_state: st.session_state.processing = False
# # if "audio_data" not in st.session_state: st.session_state.audio_data = None
# # if "error_message" not in st.session_state: st.session_state.error_message = None
# # if "show_play" not in st.session_state: st.session_state.show_play = False
# # # Use timestamp for camera key to ensure reset
# # if "camera_key" not in st.session_state: st.session_state.camera_key = f"cam_{int(time.time())}"

# # # --- Main App Logic ---

# # # Stop immediately if critical components are missing
# # if missing_keys or not BACKEND_LOADED:
# #     # Error already shown by checks above or backend import
# #     st.warning(f"Please ensure API keys ({', '.join(missing_keys)}) are set in secrets and image_backend.py is present.")
# #     st.stop()

# # # State 1: Ready to take photo (Default state)
# # if not st.session_state.show_play and not st.session_state.processing and not st.session_state.error_message:
# #     # Only show Camera Input
# #     captured_image_buffer = st.camera_input(
# #         "Tap to Take Picture", # Label text might not be visible due to CSS hiding label
# #         key=st.session_state.camera_key,
# #         label_visibility="hidden" # Explicitly hide label
# #         )

# #     # If picture is taken
# #     if captured_image_buffer is not None:
# #         st.session_state.photo_buffer = captured_image_buffer.getvalue()
# #         st.session_state.processing = True # Move to processing state
# #         st.rerun() # Rerun to show spinner

# # # State 2: Processing photo
# # elif st.session_state.processing:
# #     with st.spinner("Analyzing image and generating audio..."):
# #         # 1. Analyze Image
# #         description, analysis_error = perform_image_analysis_simple(st.session_state.photo_buffer)
# #         st.session_state.photo_buffer = None # Clear buffer immediately after use

# #         if analysis_error:
# #             # If analysis fails, set error and go back to start state
# #             st.session_state.error_message = analysis_error
# #             st.session_state.processing = False
# #             st.session_state.show_play = False
# #             st.rerun()
# #         else:
# #             # 2. Generate Audio if analysis succeeded
# #             audio_data, tts_error = text_to_speech_simple(description, DEFAULT_VOICE)
# #             if tts_error:
# #                 # If TTS fails, set error and go back to start state
# #                 st.session_state.error_message = tts_error
# #                 st.session_state.processing = False
# #                 st.session_state.show_play = False
# #                 st.rerun()
# #             else:
# #                 # 3. Success! Store audio, switch state to show play button
# #                 st.session_state.audio_data = audio_data
# #                 st.session_state.processing = False
# #                 st.session_state.show_play = True
# #                 st.rerun() # Rerun to show play button

# # # State 3: Show Play button and Audio
# # elif st.session_state.show_play:
# #     if st.session_state.audio_data:
# #         # Encode audio data for HTML component
# #         audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
# #         audio_src = f"data:audio/mpeg;base64,{audio_base64}"

# #         # --- HTML Component for LARGE Play Button + Audio Player ---
# #         component_html = f"""
# #         <div class="center-container" data-streamlit-component-button-audio>
# #              <div><button id="playButton">▶️ PLAY AUDIO</button></div>
# #              <div id="audioPlayerContainer"><audio id="audioPlayer" controls src="{audio_src}"></audio></div>
# #         </div>
# #         <script>
# #             // Ensure script runs only once or elements are found correctly
# #             const playButton = document.getElementById('playButton');
# #             const audioPlayer = document.getElementById('audioPlayer');
# #             const componentId = 'button-audio-component'; // Unique ID for this component instance logic

# #             // Check if listener is already attached using a body attribute or similar
# #             if (playButton && audioPlayer && !document.body.hasAttribute('data-listener-bound-' + componentId)) {{
# #                  playButton.addEventListener('click', function() {{
# #                      console.log("Play button clicked!");
# #                      if (audioPlayer.paused) {{
# #                          audioPlayer.play().catch(e => console.error("Audio play failed:", e));
# #                      }} else {{
# #                          audioPlayer.pause();
# #                          // Optional: reset to beginning if clicked while playing
# #                          // audioPlayer.currentTime = 0;
# #                      }}
# #                  }});
# #                  // Mark that listener has been bound for this component instance
# #                  document.body.setAttribute('data-listener-bound-' + componentId, 'true');
# #                  console.log("Event listener bound for " + componentId);
# #             }} else if (document.body.hasAttribute('data-listener-bound-' + componentId)) {{
# #                  // console.log("Event listener already bound for " + componentId); // Avoid excessive logging
# #             }} else {{
# #                  console.error("Component elements not found for binding for " + componentId + "!");
# #             }}
# #         </script>
# #         """
# #         # Adjust height: Play button (25vh) + audio player (small height, ~50px) + margins
# #         # Using a fixed height might be safer if vh causes issues across devices. 400px is a generous estimate.
# #         st.components.v1.html(component_html, height=400)

# #     else:
# #         # Fallback if audio data is somehow missing in this state
# #         st.error("Error: Audio data not available.")
# #         st.session_state.show_play = False # Force back to previous state if error occurs
# #         st.rerun()

# #     # "Start Over" Button (uses general stButton CSS for size)
# #     if st.button("🔄 START OVER", key="reset_button", type="secondary"):
# #         # Reset all relevant state variables
# #         st.session_state.photo_buffer = None
# #         st.session_state.processing = False
# #         st.session_state.audio_data = None
# #         st.session_state.error_message = None
# #         st.session_state.show_play = False
# #         # CRITICAL: Update camera key to force widget reset
# #         st.session_state.camera_key = f"cam_{int(time.time())}"
# #         st.rerun() # Go back to the initial camera view

# # # State 4: Error Display
# # elif st.session_state.error_message and not st.session_state.processing:
# #     st.error(f"An error occurred: {st.session_state.error_message}")

# #     # "Try Again" Button (uses general stButton CSS for size)
# #     if st.button("🔄 TRY AGAIN", key="try_again_button", type="secondary"): # Use secondary for consistency
# #          # Clear the error and reset camera key, go back to start state
# #          st.session_state.error_message = None
# #          st.session_state.photo_buffer = None # Ensure buffer is clear
# #          st.session_state.processing = False
# #          st.session_state.show_play = False
# #          # CRITICAL: Update camera key to force widget reset
# #          st.session_state.camera_key = f"cam_{int(time.time())}"
# #          st.rerun()

####### GPT 4o ATTEMPT *WITH* GEMINI 2.5 REFACTORING FOR BACK CAMERA INPUT
import streamlit as st
import requests
import base64
from image_backend import look_at_photo, encode_image_from_bytes # Assuming these are correct

# --- Import the new camera component ---
from streamlit_back_camera_input import back_camera_input
# --------------------------------------

# --- Config ---
st.set_page_config(page_title="Camera to Speech", layout="centered")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
VOICE = "bella"
TTS_MODEL = "tts-1"

# --- Basic Error Checking for Secrets ---
if not LEMONFOX_API_KEY:
    st.error("🚨 Error: LEMONFOX_API_KEY not found in Streamlit secrets. TTS will fail.")
    # st.stop() # Optionally stop execution if key is critical

# --- Styling ONLY for st.button ("Start Over") ---
st.markdown("""
    <style>
        /* CSS for standard st.button widgets */
        div[data-testid="stButton"] > button {
            background-color: #d32f2f; /* Red */
            color: white;
            font-size: 36px;
            padding: 10px; /* Reduced padding slightly to help text fit */
            width: 80vw;
            max-width: 600px;
            height: 150px; /* USE FIXED PX HEIGHT */
            border: none;
            border-radius: 16px;
            display: flex; /* Use flex to center content */
            align-items: center;
            justify-content: center;
            margin-left: auto;
            margin-right: auto;
            margin-top: 20px;
            box-sizing: border-box;
            line-height: 1.2; /* Help with wrapping if needed */
        }
        div[data-testid="stButton"] > button:hover {
             background-color: #b71c1c; /* Darker Red */
             color: white;
             cursor: pointer;
         }
         .stApp > div:first-child {
             padding-top: 2vh;
         }
         div[data-testid="stVerticalBlock"] {
             align-items: center;
         }
    </style>
""", unsafe_allow_html=True)
# ----------------------------------------------------------

# --- TTS ---
# (Same robust function as before)
def text_to_speech(text):
    if not LEMONFOX_API_KEY: st.error("Cannot generate speech: LEMONFOX_API_KEY is missing."); return None
    if not text: st.warning("No text description provided to generate speech."); return None
    headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
    data = {"model": TTS_MODEL, "input": text, "voice": VOICE, "response_format": "mp3"}
    try:
        with st.spinner("🔊 Generating audio description..."):
            response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
            response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e: st.error(f"Audio generation failed: {e}"); return None
    except Exception as e: st.error(f"An unexpected error occurred during TTS: {e}"); return None

# --- State Init ---
if "mode" not in st.session_state: st.session_state.mode = "camera"
if "audio_data" not in st.session_state: st.session_state.audio_data = None

# --- App Logic ---
if st.session_state.mode == "camera":
    st.info("Tap the video area below to take a picture using the back camera.")
    image_object = back_camera_input(key="back_cam_px_height")
    if image_object is not None:
        with st.spinner("Analyzing image and generating audio..."):
            try:
                image_bytes = image_object.getvalue()
                base64_image = encode_image_from_bytes(image_bytes)
                if not base64_image: st.error("Failed to encode image."); st.stop()
                description = look_at_photo(base64_image, upload=False)
                if not description or "error" in description.lower(): st.error(f"Image analysis failed: {description}"); st.stop()
                audio = text_to_speech(description)
                if audio:
                    st.session_state.audio_data = audio
                    st.session_state.mode = "result"
                    st.rerun()
                else: st.warning("Audio generation failed. Please try taking another picture."); st.stop()
            except Exception as e: st.error(f"An error occurred during processing: {e}"); st.stop()

elif st.session_state.mode == "result":
    if st.session_state.audio_data:
        audio_b64 = base64.b64encode(st.session_state.audio_data).decode("utf-8")
        # --- Updated HTML component for PLAY AUDIO button ---
        st.components.v1.html(f"""
            <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
                <button id="playAudio" style="
                    background-color: #4CAF50; /* Green */
                    color: white;
                    /* === Matching START OVER more closely === */
                    font-size: 36px;
                    padding: 10px; /* Reduced padding slightly */
                    width: 80vw;
                    max-width: 600px;
                    height: 150px; /* USE FIXED PX HEIGHT */
                    border: none;
                    border-radius: 16px;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    /* === End matching styles === */
                    margin-bottom: 15px; /* Keep reduced margin */
                    cursor: pointer;
                    line-height: 1.2; /* Help text fit */
                    text-align: center; /* Ensure text centers */
                ">▶️ PLAY AUDIO</button>

                <audio id="player" src="data:audio/mp3;base64,{audio_b64}" controls style="display:none; width: 80%; max-width: 600px;"></audio>

                <script>
                    const btn = document.getElementById("playAudio");
                    const player = document.getElementById("player");
                    if (btn && player) {{
                        if (!window.playListenerAttached) {{
                             btn.addEventListener("click", () => {{
                                if (player.paused) {{ player.play().catch(e => console.error("Audio play failed:", e)); }} else {{ player.pause(); }}
                            }});
                            window.playListenerAttached = true;
                        }}
                    }} else {{ console.error("Play button or audio player element not found!"); }}
                </script>
            </div>
        """, height=200) # Adjusted component height (150px button + 15px margin + ~35px for potential player controls if shown/debug)
        # ----------------------------------------------------
    else:
        st.error("Error: Audio data not found for playback.")

    # This button uses the CSS above
    if st.button("🔄 START OVER"):
        st.session_state.mode = "camera"
        st.session_state.audio_data = None
        st.components.v1.html("<script>window.playListenerAttached = false;</script>", height=0)
        st.rerun()
