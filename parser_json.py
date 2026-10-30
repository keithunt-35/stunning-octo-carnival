"""
JSON parser for category-aware structured output.

parse_label_response(text, category) -> dict
    Parses the model's JSON response and returns structured data
    with both English and Luganda sections, organized by category.
"""
import json
import re
from datetime import datetime, timedelta

from luganda_glossary import NOT_CLEARLY_VISIBLE_EN, NOT_CLEARLY_VISIBLE_LG


def parse_label_response(text: str, category: str | None = None) -> dict:
    """Parse the model's JSON response.
    
    Returns a dict with:
        {
            "success": bool,
            "category": str,
            "english": dict,
            "luganda": dict,
            "raw": str,
            "error": str (if parsing failed)
        }
    
    If parsing fails, falls back to raw text display.
    """
    result = {
        "success": False,
        "category": category or "other",
        "english": {},
        "luganda": {},
        "raw": text,
        "error": None,
    }
    
    if not text or not text.strip():
        result["error"] = "Empty response from model"
        return result
    
    # Try to parse as JSON
    try:
        # Clean up the text (sometimes models wrap JSON in markdown code blocks)
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        data = json.loads(cleaned)
        
        # Extract English and Luganda sections
        if "english" in data and isinstance(data["english"], dict):
            result["english"] = data["english"]
            result["success"] = True
        
        if "luganda" in data and isinstance(data["luganda"], dict):
            result["luganda"] = data["luganda"]
        
        # Infer category from the data if not provided
        if not result["category"] or result["category"] == "other":
            if "category" in result["english"]:
                result["category"] = result["english"]["category"].lower()
        
    except json.JSONDecodeError as e:
        result["error"] = f"JSON parsing failed: {e}"
        # Try to salvage partial data
        result["english"] = {"raw_text": text}
        result["luganda"] = {}
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        result["english"] = {"raw_text": text}
        result["luganda"] = {}
    
    return result


def check_expiry(expiry_str: str) -> dict:
    """Check if an expiry/best-before date has passed.
    
    Returns:
        {
            "is_expired": bool,
            "days_until_expiry": int (negative if expired),
            "formatted_date": str
        }
    """
    result = {
        "is_expired": False,
        "days_until_expiry": None,
        "formatted_date": expiry_str,
    }
    
    if not expiry_str or NOT_CLEARLY_VISIBLE_EN.lower() in expiry_str.lower():
        return result
    
    # Try common date formats
    formats = [
        "%d/%m/%Y",  # 31/12/2026
        "%m/%Y",     # 12/2026
        "%Y-%m-%d",  # 2026-12-31
        "%d-%m-%Y",  # 31-12-2026
        "%m-%Y",     # 12-2026
    ]
    
    today = datetime.now()
    
    for fmt in formats:
        try:
            expiry = datetime.strptime(expiry_str.strip(), fmt)
            # For MM/YYYY format, assume end of month
            if fmt in ("%m/%Y", "%m-%Y"):
                # Move to last day of that month
                if expiry.month == 12:
                    expiry = expiry.replace(day=31)
                else:
                    next_month = expiry.replace(month=expiry.month + 1, day=1)
                    expiry = next_month - timedelta(days=1)
            
            delta = (expiry - today).days
            result["is_expired"] = delta < 0
            result["days_until_expiry"] = delta
            result["formatted_date"] = expiry.strftime("%d %b %Y")
            return result
        except (ValueError, AttributeError):
            continue
    
    # Couldn't parse — return as-is
    return result


def count_missing_fields(data: dict) -> tuple[int, int]:
    """Count how many fields are "not clearly visible".
    
    Returns (missing_count, total_fields).
    """
    if not data:
        return 0, 0
    
    total = 0
    missing = 0
    
    for key, value in data.items():
        if key in ("category", "confidence_note", "raw_text"):
            continue  # Skip meta fields
        
        total += 1
        if isinstance(value, str) and NOT_CLEARLY_VISIBLE_EN.lower() in value.lower():
            missing += 1
    
    return missing, total


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------
def _test_parse():
    """Test JSON parsing with good and bad inputs."""
    
    # Test 1: Valid JSON
    good_json = """{
  "english": {
    "product_name": "PANADOL EXTRA",
    "category": "medicine",
    "active_ingredients": "Paracetamol 500mg, Caffeine 65mg",
    "dosage": "1-2 tablets every 4-6 hours",
    "warnings": "Keep away from children",
    "expiry_date": "12/2026"
  },
  "luganda": {
    "product_name": "PANADOL EXTRA",
    "category": "eddagala",
    "active_ingredients": "Paracetamol 500mg, Caffeine 65mg",
    "dosage": "empeera 1-2 buli ssaawa 4-6",
    "warnings": "Teeka wala n'abaana",
    "expiry_date": "12/2026"
  }
}"""
    
    result = parse_label_response(good_json, "Medicine")
    assert result["success"], "Should parse valid JSON"
    assert result["english"]["product_name"] == "PANADOL EXTRA"
    assert result["luganda"]["product_name"] == "PANADOL EXTRA"
    print("✅ Test 1 passed: Valid JSON")
    
    # Test 2: JSON wrapped in markdown
    markdown_json = """```json
{
  "english": {"product_name": "Test"},
  "luganda": {"product_name": "Test"}
}
```"""
    
    result = parse_label_response(markdown_json)
    assert result["success"], "Should parse markdown-wrapped JSON"
    print("✅ Test 2 passed: Markdown-wrapped JSON")
    
    # Test 3: Invalid JSON (fallback to raw)
    bad_json = "This is not JSON at all"
    
    result = parse_label_response(bad_json)
    assert not result["success"], "Should fail gracefully"
    assert result["error"] is not None
    assert "raw_text" in result["english"]
    print("✅ Test 3 passed: Invalid JSON fallback")
    
    # Test 4: Empty response
    result = parse_label_response("")
    assert not result["success"]
    assert result["error"] == "Empty response from model"
    print("✅ Test 4 passed: Empty response")
    
    print("\n✅ All parser tests passed!")


def _test_expiry():
    """Test expiry date checking."""
    
    # Test 1: Future date
    result = check_expiry("12/2027")
    assert not result["is_expired"], "12/2027 should not be expired"
    assert result["days_until_expiry"] > 0
    print(f"✅ Test 1: Future date - {result['days_until_expiry']} days remaining")
    
    # Test 2: Past date
    result = check_expiry("01/2020")
    assert result["is_expired"], "01/2020 should be expired"
    assert result["days_until_expiry"] < 0
    print(f"✅ Test 2: Past date - expired {abs(result['days_until_expiry'])} days ago")
    
    # Test 3: Not clearly visible
    result = check_expiry(NOT_CLEARLY_VISIBLE_EN)
    assert not result["is_expired"], "Should not mark unclear dates as expired"
    print("✅ Test 3: Unclear date handled")
    
    # Test 4: Invalid format
    result = check_expiry("sometime next year")
    assert result["formatted_date"] == "sometime next year"
    print("✅ Test 4: Invalid format returned as-is")
    
    print("\n✅ All expiry tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("PARSER TESTS")
    print("=" * 60)
    _test_parse()
    print()
    _test_expiry()
