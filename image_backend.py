import openai
import base64
import requests
import litellm
import streamlit as st  # Import streamlit

litellm.set_verbose = True


def look_at_photo(base64_image, upload=False):
    model = "gpt-4o" if upload else "gpt-4o-mini"  # Correct model selection
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"  # Use st.secrets
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """You are tasked with generating audio descriptions of photographs for vision-impaired individuals. Describe images accurately, thoroughly, yet succinctly.  List only what you see, without commentary.  Avoid phrases like "Certainly, let me describe this image for you!"."""
                    },
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Describe this photograph or image in sufficient detail for a vision-impaired individual.  Be mindful of the time it takes to read text aloud and avoid unnecessary verbosity."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4000
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            print("Response does not contain 'choices' key")
            return "An unexpected response was received from the API."
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "An error occurred while processing the image."
    except ValueError as e:
        print(f"Invalid response: {e}")
        return "An unexpected response was received from the API."
    except Exception as e: #Catch any other errors
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred."


def encode_image_from_bytes(image_bytes):
    """Encodes image bytes to base64."""
    return base64.b64encode(image_bytes).decode('utf-8')
