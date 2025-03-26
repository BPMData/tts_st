import streamlit as st
import requests
import base64
from image_backend import look_at_photo, encode_image_from_bytes # Assuming these are correct
import io

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
    # st.stop()

# --- CSS Styling for st.button (BIG) ---
st.markdown("""
    <style>
        /* Target standard Streamlit buttons */
        div[data-testid="stButton"] > button {
            background-color: #d32f2f; /* Red */
            color: white;
            font-size: 40px;  /* Increased Font Size */
            font-weight: bold; /* Make text bolder */
            padding: 15px; /* Adjust padding slightly for larger font */
            width: 85vw; /* Slightly wider */
            max-width: 650px; /* Slightly wider max */
            height: 160px; /* Slightly Taller */
            border: none;
            border-radius: 20px; /* Slightly larger radius */
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: auto;
            margin-right: auto;
            margin-top: 25px; /* More space above */
            box-sizing: border-box;
            line-height: 1.3; /* Ensure text fits */
            text-align: center;
        }
        div[data-testid="stButton"] > button:hover {
             background-color: #b71c1c; /* Darker Red */
             color: white;
             cursor: pointer;
             opacity: 0.9;
         }
         /* Basic layout centering */
         .stApp > div:first-child { padding-top: 2vh; }
         div[data-testid="stVerticalBlock"] { align-items: center; }
    </style>
""", unsafe_allow_html=True)
# ----------------------------------------------------------

# --- TTS ---
def text_to_speech(text):
    # (Same function as before)
    if not LEMONFOX_API_KEY: st.error("Cannot generate speech: LEMONFOX_API_KEY is missing."); return None, "API Key Missing"
    if not text: st.warning("No text description provided to generate speech."); return None, "No Input Text"
    headers = {"Authorization": f"Bearer {LEMONFOX_API_KEY}", "Content-Type": "application/json"}
    data = {"model": TTS_MODEL, "input": text, "voice": VOICE, "response_format": "mp3"}
    try:
        response = requests.post(LEMONFOX_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.content, None
    except requests.exceptions.RequestException as e: st.error(f"Audio generation failed: {e}"); return None, f"Audio API Error: {e}"
    except Exception as e: st.error(f"An unexpected error occurred during TTS: {e}"); return None, f"TTS Error: {e}"

# --- Image Analysis ---
def analyze_image(image_bytes):
    # (Same function as before)
    try:
        base64_image = encode_image_from_bytes(image_bytes)
        if not base64_image: return None, "Failed to encode image."
        description = look_at_photo(base64_image, upload=False)
        if not description or "error" in description.lower(): return None, f"Image analysis failed: {description}"
        return description, None
    except Exception as e: return None, f"Analysis Error: {e}"

# --- State Initialization ---
if "app_state" not in st.session_state: st.session_state.app_state = "capture"
if "image_bytes_to_process" not in st.session_state: st.session_state.image_bytes_to_process = None
if "audio_data" not in st.session_state: st.session_state.audio_data = None
if "error_message" not in st.session_state: st.session_state.error_message = None

# ==============================================================================
# --- Main App Logic based on State ---
# ==============================================================================

# --- State 1: Capture ---
if st.session_state.app_state == "capture":
    st.info("Tap the video area below to take a picture using the back camera.")
    image_object = back_camera_input(key="camera_capture_big_focus")
    if image_object is not None:
        try:
            if hasattr(image_object, 'getvalue'): st.session_state.image_bytes_to_process = image_object.getvalue()
            elif hasattr(image_object, 'read'): st.session_state.image_bytes_to_process = image_object.read()
            else: raise TypeError("Unsupported image object type.")
            if st.session_state.image_bytes_to_process:
                 st.session_state.app_state = "processing"
                 st.rerun()
            else: st.error("Captured image data could not be read.")
        except Exception as e: st.error(f"Error reading image data: {e}")

# --- State 2: Processing ---
elif st.session_state.app_state == "processing":
    with st.spinner("Analyzing image and generating audio..."):
        if st.session_state.image_bytes_to_process:
            description, analysis_err = analyze_image(st.session_state.image_bytes_to_process)
            if analysis_err:
                st.session_state.error_message = analysis_err; st.session_state.app_state = "error"
            else:
                audio, tts_err = text_to_speech(description)
                if tts_err: st.session_state.error_message = tts_err; st.session_state.app_state = "error"
                else: st.session_state.audio_data = audio; st.session_state.app_state = "playback"
            st.session_state.image_bytes_to_process = None
            st.rerun()
        else: # Should not happen
            st.error("Processing state error."); st.session_state.app_state = "capture"; st.rerun()

# --- State 3: Playback ---
elif st.session_state.app_state == "playback":
    if st.session_state.audio_data:
        audio_b64 = base64.b64encode(st.session_state.audio_data).decode("utf-8")
        # --- Play Button (HTML Component - BIG) ---
        st.components.v1.html(f"""
            <div style="display: flex; flex-direction: column; align-items: center; width: 100%;">
                <button id="playAudio" aria-label="Play Audio Description" style="
                    background-color: #4CAF50; /* Green */
                    color: white;
                    font-size: 40px; /* Increased Font Size */
                    font-weight: bold; /* Make text bolder */
                    padding: 15px; /* Match CSS padding */
                    width: 85vw; /* Slightly wider */
                    max-width: 650px; /* Slightly wider max */
                    height: 160px; /* Slightly Taller */
                    border: none;
                    border-radius: 20px; /* Slightly larger radius */
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 20px; /* Increased space below */
                    cursor: pointer;
                    line-height: 1.3; /* Ensure text fits */
                    text-align: center;
                ">▶️ PLAY AUDIO</button>
                <audio id="player" src="data:audio/mp3;base64,{audio_b64}" controls style="display:none; width: 80%; max-width: 600px;"></audio>
                <script>
                    /* Same JS as before */
                    const btn = document.getElementById("playAudio"), player = document.getElementById("player");
                    if (btn && player && !window.playListenerAttached) {{
                        btn.addEventListener("click", () => {{ if (player.paused) player.play().catch(e => console.error("Audio play failed:", e)); else player.pause(); }});
                        window.playListenerAttached = true;
                    }}
                </script>
            </div>
        """, height=250) # Increased component height to ensure button fits
        # ----------------------------------------------------
    else: # Should not happen
        st.error("Error: Audio data missing."); st.session_state.app_state = "capture"; st.rerun()

    # --- Use st.button for Start Over (Styled BIG via CSS) ---
    if st.button("🔄 START OVER", key="st_start_over_big"):
         st.session_state.app_state = "capture"
         st.session_state.audio_data = None
         st.session_state.error_message = None
         st.components.v1.html("<script>window.playListenerAttached = false;</script>", height=0)
         st.rerun()
    # ----------------------------------------------------

# --- State 4: Error ---
elif st.session_state.app_state == "error":
    st.error(f"An error occurred: {st.session_state.error_message}")

    # --- Use st.button for Try Again (Styled BIG via CSS) ---
    if st.button("🔄 TRY AGAIN", key="st_try_again_big"):
         st.session_state.app_state = "capture"
         st.session_state.error_message = None
         st.session_state.audio_data = None
         st.rerun()
    # ----------------------------------------------------
