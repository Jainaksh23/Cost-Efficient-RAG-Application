# Notes on Gemini Integration Issue

## Original Plan
The initial architecture plan specified using the Gemini API (via the `google-genai` SDK) for the LLM generation layer and LLM-as-a-judge evaluation harness. 

## Issue Encountered
When testing the integration with a genuinely valid, active Google AI Studio API key in the new `AQ.` format (e.g. `AQ.[REDACTED_EXAMPLE_KEY]`), the API repeatedly rejected the key with a `400 INVALID_ARGUMENT: API_KEY_INVALID` error. 

To isolate the issue, a minimal standalone script (`scripts/check_gemini_key.py`) was created to test the raw SDK initialization (`from google import genai; genai.Client(...)`) outside of the application logic. This script confirmed the identical `API_KEY_INVALID` failure, proving the issue was fully isolated to the Google backend authentication layer and/or SDK compatibility, rather than any logic bug in our application code.

## Root Cause
According to Google's developer forums, there is a known, currently active compatibility issue and bug on the platform side with the new "AQ." key format not being correctly authenticated by older REST API patterns and some SDK implementations, causing them to be rejected as invalid.

## Resolution
To prevent this issue from blocking development and to ensure a stable testing environment for the assignment, we have switched the LLM provider entirely to **Groq**. 
The `google-genai` dependency has been removed from `requirements.txt` and replaced with `groq`. The generation script `generation/generator.py` and configuration files have been refactored to use the Groq Python SDK, pointing by default to the `llama-3.3-70b-versatile` model.
