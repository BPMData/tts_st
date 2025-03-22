import openai
import base64
import requests
from io import BytesIO
import litellm

litell.set_verbose=True


def look_at_photos(base64_image, upload=False):
    model = "gpt-4o-mini"if not upload else "gpt-4o"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"
    }
    payload = {
        "model": model,
        "messages": [
             {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """You are being tasked with helping generate audio descriptions of photographs for the benefit of vision-impaired and blind individuals. Your role is to use machine vision to describe photographs or images you are passed as accurately as possible, thoroughly, helpfully, and yet succinctly given that the vision-impaired individuals using this tool will have to listen to whatever you write out loud. You are going to list only what you see, without commentary. For example, a good beginning of your response would be to immediately start describing what you see. A BAD beginning of your response would be: "Certainly, let me describe this image for you!", or "Okay. Well, what I can see in this image is...""""
                    },           
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """What do you see in this photograph or image? Describe in sufficient detail for a vision-impaired individual, but recognize your output will be converted into speech, so be mindful of the time it takes to read text out loud and avoid unnecessary verbosity."""
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
        "max_tokens": 4,000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Check if the request was successful
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
