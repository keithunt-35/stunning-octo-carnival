"""
Luganda translations for common product label terms.

Each entry marked "needs native speaker review" - these are AI-generated
translations that should be verified by a native Luganda speaker before
being considered authoritative.

Usage:
- Use these terms when translating product labels
- If a term is NOT in this glossary, keep the English word
- For ingredients: "wheat (eŋaano)" only if in glossary, otherwise "wheat"
"""

# Fixed phrases (use these exactly, never generate alternatives)
NOT_CLEARLY_VISIBLE_EN = "Not clearly visible"
NOT_CLEARLY_VISIBLE_LG = "Tekirabika bulungi"  # needs native speaker review

# Common terms (all categories)
COMMON_TERMS = {
    "expiry date": "lunaku lw'okukoma",  # needs native speaker review
    "best before": "kirungi okutuusa",  # needs native speaker review
    "warning": "okulabula",  # needs native speaker review
    "keep away from children": "teeka wala n'abaana",  # needs native speaker review
    "store": "tereka",  # needs native speaker review
    "storage": "okutereka",  # needs native speaker review
    "batch": "batch",  # needs native speaker review
    "manufacturer": "eyakoze",  # needs native speaker review
    "product name": "erinnya ly'ekintu",  # needs native speaker review
    "not clearly visible": NOT_CLEARLY_VISIBLE_LG,  # needs native speaker review
}

# Medicine terms
MEDICINE_TERMS = {
    "tablet": "empeera",  # needs native speaker review
    "tablets": "empeera",  # needs native speaker review
    "capsule": "kapisule",  # needs native speaker review
    "syrup": "sirupu",  # needs native speaker review
    "dose": "dosi",  # needs native speaker review
    "dosage": "dosi",  # needs native speaker review
    "twice a day": "emirundi ebiri buli lunaku",  # needs native speaker review
    "once a day": "omulundi gumu buli lunaku",  # needs native speaker review
    "three times a day": "emirundi esatu buli lunaku",  # needs native speaker review
    "after food": "oluvannyuma lw'okulya",  # needs native speaker review
    "before food": "nga tonnalidde",  # needs native speaker review
    "with water": "n'amazzi",  # needs native speaker review
    "active ingredient": "ekirimu ekikulu",  # needs native speaker review
    "active ingredients": "ebirimu ebikulu",  # needs native speaker review
    "strength": "amaanyi",  # needs native speaker review
    "directions": "ebiragiro",  # needs native speaker review
    "adults": "abakulu",  # needs native speaker review
    "children": "abaana",  # needs native speaker review
    "years": "emyaka",  # needs native speaker review
    "age": "emyaka",  # needs native speaker review
}

# Agro terms
AGRO_TERMS = {
    "pesticide": "eddagala ly'ebiwuka",  # needs native speaker review
    "herbicide": "eddagala ly'omuddo",  # needs native speaker review
    "fertilizer": "emboga",  # needs native speaker review
    "seeds": "ensigo",  # needs native speaker review
    "seed": "ensigo",  # needs native speaker review
    "spray": "fuyira",  # needs native speaker review
    "mix with water": "tabula n'amazzi",  # needs native speaker review
    "mix": "tabula",  # needs native speaker review
    "dilute": "tabula",  # needs native speaker review
    "wear gloves": "bambala gloves",  # needs native speaker review
    "gloves": "gloves",  # needs native speaker review (keep English)
    "mask": "omukunnu",  # needs native speaker review
    "protective equipment": "ebikuuma",  # needs native speaker review
    "keep away from animals": "teeka wala n'ebisolo",  # needs native speaker review
    "animals": "ebisolo",  # needs native speaker review
    "harvest": "kunkula",  # needs native speaker review
    "harvest interval": "ekiseera ky'okukungula",  # needs native speaker review
    "re-entry interval": "ekiseera ky'okudda mu kifo",  # needs native speaker review
    "application rate": "omuwendo gw'okukozesa",  # needs native speaker review
    "per hectare": "buli hectare",  # needs native speaker review
    "hectare": "hectare",  # needs native speaker review (keep English)
    "crop": "ekirime",  # needs native speaker review
    "weeds": "omuddo",  # needs native speaker review
    "pests": "ebiwuka",  # needs native speaker review
}

# Food terms
FOOD_TERMS = {
    "ingredients": "ebirimu",  # needs native speaker review
    "allergy": "obulwadde bwa allergy",  # needs native speaker review
    "allergen": "ekintu ekivaamu obulwadde bwa allergy",  # needs native speaker review
    "allergens": "ebintu ebiva mu obulwadde bwa allergy",  # needs native speaker review
    "contains": "kirimu",  # needs native speaker review
    "nutrition": "ebiryo",  # needs native speaker review
    "energy": "amaanyi",  # needs native speaker review
    "protein": "protein",  # needs native speaker review (keep English)
    "fat": "amasavu",  # needs native speaker review
    "sugar": "sucre",  # needs native speaker review
    "salt": "omunnyo",  # needs native speaker review
    "store in a cool place": "tereka mu kifo ekinyogovu",  # needs native speaker review
    "cool place": "kifo ekinyogovu",  # needs native speaker review
    "dry place": "kifo ekitali n'obunyevu",  # needs native speaker review
    "refrigerate": "teeka mu fridge",  # needs native speaker review
    "after opening": "oluvannyuma lw'okufungula",  # needs native speaker review
    "use within": "kikyale mu",  # needs native speaker review
    "net weight": "obuzito",  # needs native speaker review
    "volume": "bungi",  # needs native speaker review
}

# Common food ingredients (for reference, keep English if not listed)
INGREDIENT_TERMS = {
    "wheat": "eŋaano",  # needs native speaker review
    "maize": "ebigaati",  # needs native speaker review
    "rice": "omuceere",  # needs native speaker review
    "beans": "ebijanjaalo",  # needs native speaker review
    "milk": "amata",  # needs native speaker review
    "water": "amazzi",  # needs native speaker review
    "salt": "omunnyo",  # needs native speaker review
    "sugar": "sucre",  # needs native speaker review
    "oil": "amafuta",  # needs native speaker review
    "sunflower": "enjuba",  # needs native speaker review
}

# Combine all glossaries for easy lookup
ALL_TERMS = {
    **COMMON_TERMS,
    **MEDICINE_TERMS,
    **AGRO_TERMS,
    **FOOD_TERMS,
    **INGREDIENT_TERMS,
}


def get_luganda(english_term: str, default: str = None) -> str | None:
    """Look up a Luganda translation for an English term.
    
    Args:
        english_term: English word or phrase (case-insensitive)
        default: Default value if not found (None means return None)
    
    Returns:
        Luganda translation if found, otherwise default
    """
    term = english_term.lower().strip()
    return ALL_TERMS.get(term, default)


def format_with_luganda(english_term: str) -> str:
    """Format a term with Luganda translation if available.
    
    Args:
        english_term: English word or phrase
    
    Returns:
        "english (luganda)" if translation exists, otherwise "english"
    
    Examples:
        format_with_luganda("wheat") → "wheat (eŋaano)"
        format_with_luganda("xanthan gum") → "xanthan gum"
    """
    luganda = get_luganda(english_term)
    if luganda and luganda != english_term.lower():
        return f"{english_term} ({luganda})"
    return english_term


def export_to_csv(filename: str = "review_sheet.csv"):
    """Export all glossary terms to CSV for native speaker review.
    
    Creates a CSV with columns: English | Luganda | Category | Status
    """
    import csv
    
    rows = []
    
    # Add common terms
    for eng, lug in COMMON_TERMS.items():
        rows.append([eng, lug, "Common", "needs native speaker review"])
    
    # Add medicine terms
    for eng, lug in MEDICINE_TERMS.items():
        rows.append([eng, lug, "Medicine", "needs native speaker review"])
    
    # Add agro terms
    for eng, lug in AGRO_TERMS.items():
        rows.append([eng, lug, "Agro-input", "needs native speaker review"])
    
    # Add food terms
    for eng, lug in FOOD_TERMS.items():
        rows.append([eng, lug, "Food", "needs native speaker review"])
    
    # Add ingredient terms
    for eng, lug in INGREDIENT_TERMS.items():
        rows.append([eng, lug, "Food (Ingredients)", "needs native speaker review"])
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["English", "Luganda", "Category", "Status"])
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} terms to {filename} for native speaker review")


if __name__ == "__main__":
    # Test the glossary
    print("Luganda Glossary Test")
    print("=" * 60)
    
    test_terms = [
        "tablet", "pesticide", "ingredients", "wheat", "xanthan gum",
        "warning", "not clearly visible", "children"
    ]
    
    for term in test_terms:
        luganda = get_luganda(term)
        formatted = format_with_luganda(term)
        print(f"{term:20} → {luganda if luganda else '(not in glossary)':30} | {formatted}")
    
    print("\n" + "=" * 60)
    print("Exporting to CSV...")
    export_to_csv()
