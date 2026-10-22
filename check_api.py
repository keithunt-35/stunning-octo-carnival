"""
Phase 0 — Environment & API check.

This script:
  1. Loads your GOOGLE_API_KEY from .env
  2. Lists the models your key can access
  3. Confirms which Gemma 4 model IDs (gemma-4-26b-a4b-it, gemma-4-31b-it) work
  4. Does one text-only test call and prints the reply

Run:
    python check_api.py
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Check the API key
# ---------------------------------------------------------------------------
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("ERROR: GOOGLE_API_KEY is not set (or is still the placeholder).")
    print("  1. Get a free key at: https://aistudio.google.com/apikey")
    print("  2. Edit the .env file and replace the placeholder:")
    print("     GOOGLE_API_KEY=AIzaSy...your_real_key...")
    sys.exit(1)

print("API key found. Length:", len(api_key), "chars\n")

# ---------------------------------------------------------------------------
# 2. Create the client and list available models
# ---------------------------------------------------------------------------
from google import genai  # imported after the key check so the error msg is clean

client = genai.Client(api_key=api_key)

# The two Gemma 4 models we care about (confirmed real model IDs).
CANDIDATES = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]

print("=" * 55)
print("Checking which Gemma 4 models your key can use...")
print("=" * 55)

available = set()
try:
    for m in client.models.list():
        # m.name looks like "models/gemma-4-26b-a4b-it" — strip the prefix
        available.add(m.name.replace("models/", ""))
    print(f"Total models visible to your key: {len(available)}\n")
except Exception as e:
    print(f"Could not list models ({e}). Will try the candidates directly.\n")

working = []
for candidate in CANDIDATES:
    if candidate in available:
        print(f"  [OK]  {candidate}  — available")
        working.append(candidate)
    else:
        print(f"  [--]  {candidate}  — not in the model list (will still try it)")

# Also list every Gemma model for reference
gemma_models = sorted(m for m in available if "gemma" in m.lower())
if gemma_models:
    print("\nAll Gemma models visible to your key:")
    for m in gemma_models:
        print(f"  - {m}")

# ---------------------------------------------------------------------------
# 3. Pick a working model and do a text-only test call
# ---------------------------------------------------------------------------
# If neither showed up in the list, try the first candidate anyway
# (some keys can use a model even if it doesn't appear in models.list()).
if not working:
    print("\nNo Gemma 4 model found in the list — trying first candidate anyway...")
    working = [CANDIDATES[0]]

model_id = working[0]
print(f"\n{'=' * 55}")
print(f"Test text call with model: {model_id}")
print(f"{'=' * 55}")

try:
    response = client.models.generate_content(
        model=model_id,
        contents="Say hello in one short sentence.",
    )
    reply = response.text
    if reply:
        print("Reply received!")
        print(f"\n>>> {reply.strip()}\n")
        print("=" * 55)
        print(f"WORKING MODEL ID: {model_id}")
        print("=" * 55)
        print("Phase 0 complete. Save this model ID for the later phases.")
    else:
        print("WARNING: Response text was empty.")
        finish = (
            response.candidates[0].finish_reason
            if response.candidates
            else "unknown"
        )
        print(f"Finish reason: {finish}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Test call failed: {e}")
    sys.exit(1)
