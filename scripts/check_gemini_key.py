"""
scripts/check_gemini_key.py
Minimal sanity-check script to test the Gemini API key with the new SDK pattern.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google import genai
import config

def main():
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents="Say the word OK and nothing else."
        )
        print(response.text)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
