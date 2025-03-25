import streamlit as st
import base64
from image_backend import look_at_photo, encode_image_from_bytes
import requests

# Config
st.set_page_config(page_title="Camera to Speech", layout="wide")
LEMONFOX_API_KEY = st.secrets.get("LEMONFOX_API_KEY")
LEMONFOX_API_URL = "https://api.lemonfox.ai/v1/audio/speech"
VOICE = "bella"
TTS_MODEL = "tts-1"

# Session state init
if "mode" not in st.session_state:
    st.session_state.mode = "camera"
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# TTS function
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

# Analyze image
def analyze_image_and_generate_audio(image_bytes):
    base64_image = encode_image_from_bytes(image_bytes)
    description = look_at_photo(base64_image, upload=False)
    if description:
        return text_to_speech(description)
    return None

# Main flow
if st.session_state.mode == "camera":
    image = st.camera_input("Take a photo")
    if image is not None:
        st.session_state.audio_data = analyze_image_and_generate_audio(image.getvalue())
        st.session_state.mode = "result"
        st.rerun()

elif st.session_state.mode == "result":
    if st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format="audio/mp3")
    if st.button("🔁 Start Over"):
        st.session_state.mode = "camera"
        st.session_state.audio_data = None
        st.rerun()
