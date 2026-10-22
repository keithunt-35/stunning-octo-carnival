"""
Test script for the Gemma client.

Finds an image in test_samples/ (or uses a path you pass on the command line),
runs read_label() on it, and prints the raw model output.

Usage:
    python test_client.py                     # uses the first image in test_samples/
    python test_client.py path/to/photo.jpg   # uses a specific image
"""
import sys
import os

from gemma_client import read_label, LabelReaderError

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
    # Allow a custom image path from the command line
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = find_test_image()

    if not image_path or not os.path.exists(image_path):
        print("No test image found.")
        print("Put a real label photo (JPG/PNG) in the test_samples/ folder,")
        print("or pass a path:  python test_client.py path/to/photo.jpg")
        sys.exit(1)

    print(f"Reading image: {image_path}\n")
    print("=" * 60)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Use "Medicine / Dawa" as a default category for the test
    category = "Medicine / Dawa"

    try:
        result = read_label(image_bytes, category)
        print("SUCCESS — model returned:\n")
        print(result)
        print("\n" + "=" * 60)
        print("If you can see === ENGLISH === and === LUGANDA === sections,")
        print("Phase 2 is working correctly.")
    except LabelReaderError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
