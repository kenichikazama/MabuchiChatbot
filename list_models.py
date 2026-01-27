"""List available Gemini models"""
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("=" * 60)
print("AVAILABLE GEMINI MODELS")
print("=" * 60)

for model in client.models.list():
    print(f"\n📌 {model.name}")
    if hasattr(model, 'display_name'):
        print(f"   Display: {model.display_name}")
    if hasattr(model, 'supported_actions'):
        print(f"   Actions: {model.supported_actions}")
