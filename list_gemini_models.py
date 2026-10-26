
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("GOOGLE_API_KEY not found. Check your .env file.")
else:
    client = genai.Client(api_key=api_key)

    print("Models supporting text generation:\n")

    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(model.name)
