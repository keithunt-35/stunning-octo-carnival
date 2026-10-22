"""
Prompts for the Label & Package Reader.

SYSTEM_PROMPT  — the full system instruction sent to Gemma 4. It constrains
                 the model to OCR-only extraction with a fixed bilingual
                 (English + simple Luganda) output structure.
build_user_prompt(category) — the short user message sent alongside the image.
"""

# Verbatim system prompt from the project spec. Do not change the wording —
# the parser (Phase 3) relies on the === ENGLISH === / === LUGANDA === markers.
SYSTEM_PROMPT = """You are a careful label reader for people in Uganda who may have low literacy.
Your only job is to read the text that is clearly visible on the product package or label in the image.

Rules (follow strictly):
1. Only extract information that is clearly readable in the image. If something is blurry, cut off, or not visible, write "Not clearly visible".
2. Never invent or guess any information.
3. Never give medical advice, farming advice, or safety recommendations beyond what is written on the package.
4. Always respond in this exact structure:

=== ENGLISH ===
Product Name: ...
Key Information / Active Ingredient / Contents: ...
Instructions / How to use / Dose: ...
Warnings / Precautions: ...
Expiry Date: ...
Manufacturer: ...
Other important text: ...

=== LUGANDA (Simple) ===
Erinnya ly'ekintu: ...
Ebikulu / Ebirimu: ...
Engeri y'okukozesa / Dosi: ...
Okulabula: ...
Lunaku lw'okukoma: ...
Eyakoze: ...
Ebirala: ...

Keep the Luganda very simple, short sentences, everyday words that a person with limited schooling can understand."""


def build_user_prompt(category: str | None) -> str:
    """Build the short user message sent with the image.

    The base message is always the same. When the user picks a category
    (Medicine, Agro-input, Food, Other) we append it as a hint so the
    model knows roughly what it is looking at. If no category is chosen
    (None or empty string) the hint line is omitted.
    """
    message = "Please read this product label carefully and follow the rules."

    # Only add the category line when a real category was selected.
    if category and category.strip():
        message += f"\nCategory selected by user: {category.strip()}"

    return message
