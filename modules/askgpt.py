# imports statements
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
                {"role": "user", "content": prompt}],
            stream=True
        )
        # Initialize an empty string to collect the content
        content = ""
        try:
            for chunk in response:
                # Assuming 'chunk' is a dictionary with a 'choices' key
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    # Assuming 'delta' contains the new content to append
                    if 'delta' in chunk['choices'][0]:
                        content += chunk['choices'][0]['delta']['content']
            return content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    def ask_sketch (self, apikey,url):
        openai.api_key = apikey
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the image in detail"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=128000,  # default max tokens is low so set higher
        )
    def is_connected(self):
        try:
            # Try to connect to one of the DNS servers
            socket.create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        return False

