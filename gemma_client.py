"""
Gemma client — the core engine for reading product labels.

read_label(image_bytes, category) -> str
    Preprocesses the image, sends it to Gemma 4 with the system prompt,
    and returns the raw text response (English + Luganda sections).

All user-facing errors are raised as LabelReaderError with a friendly
message so the UI (Phase 4) can show them directly.
"""
import io
import os
import time

from dotenv import load_dotenv
from PIL import Image, ImageOps

from google import genai
from google.genai import types

from prompts import build_system_prompt, build_user_prompt

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
MODEL_ID = "gemma-4-26b-a4b-it"  # verified working in Phase 0
TEMPERATURE = 0.1                # low = faithful extraction, not creative
MAX_SIDE = 1600                  # resize longest side to this many pixels
JPEG_QUALITY = 85                # compression quality
MAX_RETRIES = 3                  # retries for transient 500 / timeout errors
RETRY_DELAY = 2                  # seconds between retries
REQUEST_TIMEOUT_MS = 60_000      # 60s per request — prevents infinite hangs


class LabelReaderError(Exception):
    """A user-facing error with a friendly message."""


# ------------------------------------------------------------------
# Image preprocessing
# ------------------------------------------------------------------
def preprocess_image(image_bytes: bytes) -> bytes:
    """Turn raw image bytes into clean, compressed JPEG bytes.

    Steps:
      1. Fix EXIF rotation (phone photos often have rotation tags).
      2. Convert RGBA / P / LA to RGB, pasting on a white background so
         transparent PNGs don't crash when saved as JPEG.
      3. Resize so the longest side is ~1600px (keeps aspect ratio).
      4. Save as JPEG at 85% quality.

    Returns JPEG bytes ready for the API.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # 1. Fix EXIF rotation
    img = ImageOps.exif_transpose(img)

    # 2. Convert to RGB, handling transparency
    if img.mode in ("RGBA", "LA"):
        # Has an alpha channel — paste on white using alpha as mask
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode == "P":
        # Palette mode — may have transparency
        if "transparency" in img.info:
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            img = background
        else:
            img = img.convert("RGB")
    elif img.mode != "RGB":
        # Any other mode (L, CMYK, etc.)
        img = img.convert("RGB")

    # 3. Resize if larger than MAX_SIDE on the longest edge
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        if w >= h:
            new_w, new_h = MAX_SIDE, round(h * MAX_SIDE / w)
        else:
            new_h, new_w = MAX_SIDE, round(w * MAX_SIDE / h)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 4. Save as JPEG
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


# ------------------------------------------------------------------
# API call
# ------------------------------------------------------------------
def _call_api(client, jpeg_bytes: bytes, user_prompt: str, system_prompt: str):
    """Call the Gemma model with retries for transient 500 errors.

    Returns the response object. Raises LabelReaderError on failure.
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    types.Part.from_bytes(
                        data=jpeg_bytes, mime_type="image/jpeg"
                    ),
                    user_prompt,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                    response_mime_type="application/json",
                ),
            )
            return response
        except LabelReaderError:
            raise  # never catch our own errors
        except Exception as e:
            last_error = e
            err_str = str(e).upper()

            # Rate limit / quota — don't retry, tell the user to wait
            if "429" in err_str or "QUOTA" in err_str or "RESOURCE" in err_str:
                raise LabelReaderError(
                    "Rate limit or quota reached. Please wait a minute "
                    "and try again."
                ) from e

            # Auth / permission — check the API key
            if "401" in err_str or "403" in err_str or "PERMISSION" in err_str or "API_KEY" in err_str or "API KEY" in err_str:
                raise LabelReaderError(
                    "API key problem. Check that GOOGLE_API_KEY in .env "
                    "is correct (get one at https://aistudio.google.com/apikey)."
                ) from e

            # Transient server error (500/502/503/504) or request timeout — retry
            if any(code in err_str for code in (
                "500", "502", "503", "504", "INTERNAL",
                "UNAVAILABLE", "TIMEOUT", "TIMED OUT",
            )):
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                raise LabelReaderError(
                    f"The Gemma API is having server issues. "
                    f"Tried {MAX_RETRIES} times. Try again in a few minutes."
                ) from e

            # Network error (DNS failure, connection refused, unreachable, etc.)
            if any(w in err_str for w in (
                "CONNECTION", "NETWORK", "REFUSED", "UNREACHABLE",
                "NODENAME", "SERVNAME", "GETADDRINFO", "NAME OR SERVICE",
                "RESOLVE", "SOCKET", "ERRNO",
            )):
                raise LabelReaderError(
                    "Network problem — check your internet connection."
                ) from e

            # Anything else
            raise LabelReaderError(f"Unexpected error calling the API: {e}") from e

    raise LabelReaderError(
        f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


def _extract_text(response) -> str:
    """Safely extract text from the API response.

    Raises LabelReaderError for empty or blocked responses.
    """
    # No candidates at all — fully blocked
    if not response.candidates:
        raise LabelReaderError(
            "The model returned no response. The image may have been "
            "blocked by safety filters — try a clearer photo of the label."
        )

    candidate = response.candidates[0]
    finish_reason = candidate.finish_reason
    reason_str = str(finish_reason).upper() if finish_reason else ""

    # Try to get text (response.text can raise if blocked)
    try:
        text = response.text
    except Exception:
        text = ""

    if text and text.strip():
        return text.strip()

    # Empty text — figure out why
    if "SAFETY" in reason_str or "BLOCK" in reason_str:
        raise LabelReaderError(
            "The model blocked this image (safety filter). "
            "Try a clearer, more focused photo of just the label."
        )
    if "RECITATION" in reason_str:
        raise LabelReaderError(
            "The model blocked this response (recitation filter). Try again."
        )

    raise LabelReaderError(
        f"The model returned an empty response (reason: {finish_reason}). "
        "The image may be too blurry or unclear — try retaking the photo."
    )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def _get_api_key() -> str | None:
    """Get the API key from st.secrets (Streamlit Cloud) or .env (local).

    Checks st.secrets first, then falls back to the .env file.
    Returns None if no key is found.
    """
    # Try Streamlit secrets first (Streamlit Community Cloud, or local
    # .streamlit/secrets.toml)
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass  # Not in a Streamlit script context (e.g., test_client.py)

    # Fall back to .env (local development)
    load_dotenv()
    return os.getenv("GOOGLE_API_KEY")


def read_label(image_bytes: bytes, category: str | None = None) -> str:
    """Read a product label from image bytes using Gemma 4.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG, WebP, etc.).
        category:    Optional category hint ("Medicine", "Agro-input",
                     "Food", "Other") or None.

    Returns:
        The raw model text containing the English and Luganda sections.

    Raises:
        LabelReaderError: For any user-facing problem (missing key,
                         rate limit, network, blocked response, etc.).
    """
    # 1. Load and check the API key (st.secrets on Cloud, .env locally)
    api_key = _get_api_key()
    if not api_key or api_key == "your_api_key_here":
        raise LabelReaderError(
            "GOOGLE_API_KEY is not set. Add it to Streamlit secrets "
            "(Cloud) or .env (local). Get one at "
            "https://aistudio.google.com/apikey."
        )

    # 2. Preprocess the image
    try:
        jpeg_bytes = preprocess_image(image_bytes)
    except Exception as e:
        raise LabelReaderError(
            f"Could not read the image file. Make sure it's a valid "
            f"photo (JPG, PNG, or WebP). (Details: {e})"
        ) from e

    # 3. Build the prompts (category-aware)
    system_prompt = build_system_prompt(category)
    user_prompt = build_user_prompt(category)

    # 4. Call the API (with a 60s request timeout so calls can't hang forever)
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )
    response = _call_api(client, jpeg_bytes, user_prompt, system_prompt)

    # 5. Extract and return the text
    return _extract_text(response)
