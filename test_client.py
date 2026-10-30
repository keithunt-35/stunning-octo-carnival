"""
Test script for the Gemma client - JSON Pipeline Version.

Tests the complete JSON pipeline: image → read_label → parse_json → display

Usage:
    python test_client.py                                    # uses first image, Medicine
    python test_client.py path/to/photo.jpg Food             # specific image and category
    python test_client.py test_samples/images---.jpg Food    # test food label
"""
import sys
import os
import json

from gemma_client import read_label, LabelReaderError
from parser_json import parse_label_response, count_missing_fields, check_expiry

# Image extensions we accept
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")


def find_test_image() -> str | None:
    """Return the path of the first image file in test_samples/, or None."""
    test_dir = os.path.join(os.path.dirname(__file__), "test_samples")
    if os.path.isdir(test_dir):
        for name in sorted(os.listdir(test_dir)):
            if name.lower().endswith(IMAGE_EXTS):
                return os.path.join(test_dir, name)
    return None


def main():
    # Parse command-line arguments
    image_path = None
    category = "Medicine / Dawa"  # Default
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = find_test_image()
    
    if len(sys.argv) > 2:
        category = sys.argv[2]
        # Normalize category if needed
        if category.lower() in ("food", "emmere"):
            category = "Food / Emmere"
        elif category.lower() in ("agro", "ebirime", "agro-input"):
            category = "Agro-input / Ebirime"
        elif category.lower() in ("medicine", "dawa"):
            category = "Medicine / Dawa"
        elif category.lower() in ("other", "ebindala"):
            category = "Other / Ebindala"

    if not image_path or not os.path.exists(image_path):
        print("No test image found.")
        print("Usage:")
        print("  python test_client.py                                    # first image, Medicine")
        print("  python test_client.py path/to/photo.jpg Food             # specific image and category")
        print("  python test_client.py test_samples/images---.jpg Food    # test food label")
        sys.exit(1)

    print("=" * 70)
    print("JSON PIPELINE TEST")
    print("=" * 70)
    print(f"Image:    {image_path}")
    print(f"Category: {category}")
    print("=" * 70)
    print()

    # Read image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Call API
    try:
        print("Sending to Gemma 4 API...")
        raw_text = read_label(image_bytes, category)
        print("Received response from API\n")
        
        # Parse JSON
        print("Parsing JSON response...")
        parsed = parse_label_response(raw_text, category)
        
        if not parsed["success"]:
            print(f"JSON PARSING FAILED: {parsed['error']}")
            print("\nRaw output:")
            print(parsed["raw"][:500])
            sys.exit(1)
        
        print("Successfully parsed JSON\n")
        
        # Display results
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        english = parsed["english"]
        luganda = parsed["luganda"]
        
        print(f"\nCategory: {parsed['category']}")
        
        # Count missing fields
        missing, total = count_missing_fields(english)
        print(f"Field clarity: {total - missing}/{total} fields clear ({missing} missing)")
        
        # English fields
        print("\n" + "=" * 70)
        print("ENGLISH FIELDS")
        print("=" * 70)
        for key, value in english.items():
            if key in ("category", "confidence_note", "raw_text"):
                continue
            status = "[!]" if "not clearly visible" in str(value).lower() else "[+]"
            # Check expiry
            if key in ("expiry_date", "best_before"):
                expiry_info = check_expiry(str(value))
                if expiry_info["is_expired"]:
                    status = "[X]"
            print(f"{status} {key:25} {str(value)[:80]}")
        
        # Luganda fields
        print("\n" + "=" * 70)
        print("LUGANDA FIELDS")
        print("=" * 70)
        for key, value in luganda.items():
            if key in ("category", "confidence_note", "raw_text"):
                continue
            status = "[!]" if "tekirabika" in str(value).lower() else "[+]"
            # Check expiry
            if key in ("expiry_date", "best_before"):
                expiry_info = check_expiry(str(value))
                if expiry_info["is_expired"]:
                    status = "[X]"
            print(f"{status} {key:25} {str(value)[:80]}")
        
        # Show raw JSON for debugging
        print("\n" + "=" * 70)
        print("RAW JSON (for debugging)")
        print("=" * 70)
        print(json.dumps({"english": english, "luganda": luganda}, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        
        if missing > total / 2:
            print("\nWarning: More than half the fields are unclear.")
            print("   Suggest retaking the photo with better lighting/focus.")
        
    except LabelReaderError as e:
        print(f"LABEL READER ERROR:")
        print(f"   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
