# imports statements
import base64

import requests
from PyQt5.QtWidgets import *
import os
import subprocess
import sys
import socket
import time

# Check for and try to import openai
try:
    import openai

    if openai.__version__ != "1.27.0":
        raise ImportError
        print("openai is already installed")
except ImportError:
    print("openai is not installed, installing...")
    if sys.platform.startswith("win"):
        subprocess.call(["pip", "install", "openai==1.27.0"], shell=False)
    elif sys.platform.startswith("darwin"):
        subprocess.call(["python3", "-m", "pip", "install", "openai==1.27.0"], shell=False)
    elif sys.platform.startswith("linux"):
        subprocess.call(["pip", "install", "openai==1.27.0"], shell=False)
    else:
        raise Exception(f"Unsupported platform: {sys.platform}")
    print("openai installed successfully")

# openai is now globally imported
import openai
from openai import OpenAI


import os
class GPT(QWidget):

    def __init__(self,parent):
        super().__init__(parent)

    def ask_gpt(self,prompt,apikey,model):
        #openai.api_key = apikey
        os.environ["OPENAI_API_KEY"] = apikey
        client = OpenAI()



        response= client.chat.completions.create(
            model = model,
            messages = [

                        {"role": "user", "content": prompt}
            ],
            stream=True
        )
        try:
            content=''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="")
                    content+=chunk.choices[0].delta.content
            return content
        except requests.exceptions.JSONDecodeError as e:
            print("Error decoding JSON response:", e)

            return None


    def ask_sketch (self, prompt,apikey,url):
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        openai.api_key = apikey
        base64_image = encode_image(url)
        # Set headers for the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        }

        # Payload for the API request
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }

        # Send the request to the OpenAI API
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        # Check for HTTP errors
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return

        # Try to parse the JSON response
        try:
            response_json = response.json()
            content = ""
            for choice in response_json['choices']:
                content += choice['message']['content']
            return content
        except requests.exceptions.JSONDecodeError as e:
            print("Error decoding JSON response:", e)
            print("Response text:", response.text)
            return None
    def is_connected(self):
        try:
            # Try to connect to one of the DNS servers
            socket.create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        return False

