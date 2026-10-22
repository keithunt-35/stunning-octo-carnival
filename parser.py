"""
Output parser for the Label & Package Reader.

split_sections(text) -> {"english": str, "luganda": str, "raw": str}

Splits the model's response into the English and Luganda sections using the
=== ENGLISH === and === LUGANDA (Simple) === markers. If the markers are
missing or slightly different, it falls back to the raw text — it never
raises an exception.
"""
import re

# Case-insensitive patterns. [^=]* lets the markers have extra text
# between the word and the closing === (e.g. "LUGANDA (Simple)").
_ENGLISH_RE = re.compile(r"===\s*ENGLISH[^=]*===", re.IGNORECASE)
_LUGANDA_RE = re.compile(r"===\s*LUGANDA[^=]*===", re.IGNORECASE)
# Catches any === SOMETHING === marker (used to find where a section ends)
_ANY_MARKER_RE = re.compile(r"===\s*\w[^=]*===", re.IGNORECASE)


def split_sections(text: str) -> dict:
    """Split model output into English and Luganda sections.

    Returns a dict with three keys:
        "english"  — the English section text (empty if marker not found)
        "luganda"  — the Luganda section text (empty if marker not found)
        "raw"      — the full original text (always present)

    If neither marker is found, the full text is put in "english" as a
    fallback so the UI has something to display.
    """
    result = {"english": "", "luganda": "", "raw": text}

    if not text or not text.strip():
        return result

    eng_match = _ENGLISH_RE.search(text)
    lug_match = _LUGANDA_RE.search(text)

    if eng_match and lug_match:
        # --- Both markers found: split between them ---
        # Make sure English comes before Luganda (it should, per the prompt)
        if eng_match.start() < lug_match.start():
            english_section = text[eng_match.end():lug_match.start()].strip()
            # Luganda runs from after its marker to the next === marker (or end)
            after_luganda = text[lug_match.end():]
            next_marker = _ANY_MARKER_RE.search(after_luganda)
            if next_marker:
                luganda_section = after_luganda[:next_marker.start()].strip()
            else:
                luganda_section = after_luganda.strip()
        else:
            # Unusual case: Luganda came first — swap them
            luganda_section = text[lug_match.end():eng_match.start()].strip()
            after_english = text[eng_match.end():]
            next_marker = _ANY_MARKER_RE.search(after_english)
            if next_marker:
                english_section = after_english[:next_marker.start()].strip()
            else:
                english_section = after_english.strip()

        result["english"] = english_section
        result["luganda"] = luganda_section

    elif eng_match:
        # --- Only English marker — take everything after it ---
        after_english = text[eng_match.end():]
        next_marker = _ANY_MARKER_RE.search(after_english)
        if next_marker:
            result["english"] = after_english[:next_marker.start()].strip()
        else:
            result["english"] = after_english.strip()

    elif lug_match:
        # --- Only Luganda marker — take everything after it ---
        after_luganda = text[lug_match.end():]
        next_marker = _ANY_MARKER_RE.search(after_luganda)
        if next_marker:
            result["luganda"] = after_luganda[:next_marker.start()].strip()
        else:
            result["luganda"] = after_luganda.strip()

    else:
        # --- No markers found — fall back to raw text in "english" ---
        result["english"] = text.strip()

    return result


# ---------------------------------------------------------------------
# Simple assert-based tests
# Run: python parser.py
# ---------------------------------------------------------------------
def _run_tests():
    # Test 1: Good output with both markers (the normal case)
    good = """=== ENGLISH ===
Product Name: PANADOL EXTRA
Key Information / Active Ingredient / Contents: Paracetamol 500mg
Instructions / How to use / Dose: 1-2 tablets every 4-6 hours
Warnings / Precautions: Keep out of reach of children
Expiry Date: 12/2026
Manufacturer: GlaxoSmithKline
Other important text: Store below 25C

=== LUGANDA (Simple) ===
Erinnya ly'ekintu: PANADOL EXTRA
Ebikulu / Ebirimu: Paracetamol 500mg
Engeri y'okukozesa / Dosi: emmeesa 1-2 buli ssaawe 4-6
Okulabula: Siiya abaana bafune
Lunaku lw'okukoma: 12/2026
Eyakoze: GlaxoSmithKline
Ebirala: Sika mu kifo ekisukka 25C"""

    r = split_sections(good)
    assert "PANADOL EXTRA" in r["english"], "English section missing product name"
    assert "Paracetamol" in r["english"], "English section missing ingredient"
    assert "Erinnya" in r["luganda"], "Luganda section missing"
    assert "Sika mu kifo" in r["luganda"], "Luganda section missing last line"
    assert r["raw"] == good, "Raw should be the full original text"
    # English should NOT contain Luganda text and vice versa
    assert "Erinnya" not in r["english"], "English leaked into Luganda"
    assert "Product Name" not in r["luganda"], "Luganda leaked into English"
    print("Test 1 passed: good output with both markers")

    # Test 2: Malformed output — no markers at all
    bad = "This is just plain text with no markers whatsoever."
    r = split_sections(bad)
    assert r["english"] == bad, "Fallback should put raw in english"
    assert r["luganda"] == "", "Luganda should be empty"
    assert r["raw"] == bad, "Raw should be original"
    print("Test 2 passed: malformed output (no markers) — fallback to raw")

    # Test 3: Only English marker (Luganda missing)
    eng_only = """=== ENGLISH ===
Product Name: Something
Expiry Date: 01/2027"""
    r = split_sections(eng_only)
    assert "Something" in r["english"], "English section should be parsed"
    assert r["luganda"] == "", "Luganda should be empty"
    print("Test 3 passed: only English marker present")

    # Test 4: Slightly different marker spelling (lowercase, no "(Simple)")
    varied = """=== english ===
Product Name: Test

=== luganda ===
Erinnya: Test"""
    r = split_sections(varied)
    assert "Test" in r["english"], "Should match lowercase 'english' marker"
    assert "Erinnya" in r["luganda"], "Should match 'luganda' without (Simple)"
    print("Test 4 passed: markers with different casing/format")

    # Test 5: Empty string
    r = split_sections("")
    assert r == {"english": "", "luganda": "", "raw": ""}, "Empty input should give empty dict"
    print("Test 5 passed: empty string")

    # Test 6: Extra text before the first marker
    with_prefix = """Here is what I found on the label:

=== ENGLISH ===
Product Name: Thing

=== LUGANDA (Simple) ===
Erinnya: Thing"""
    r = split_sections(with_prefix)
    assert "Here is what I found" not in r["english"], "Prefix should not be in English section"
    assert "Thing" in r["english"], "English section should have the product name"
    assert "Erinnya" in r["luganda"], "Luganda section should be parsed"
    print("Test 6 passed: extra text before markers is excluded")

    print("\nAll parser tests passed!")


if __name__ == "__main__":
    _run_tests()
