import json

def main():
    """
    Create and save a rule-based dictionary of the 14 major allergens
    (EU/UK standard, overlapping with US top allergens).
    """
    
    allergen_dict = {
        "Gluten": [
            "wheat", "flour", "barley", "rye", "oats", "spelt", "kamut", "semolina",
            "malt", "triticale"
        ],
        "Milk": [
            "milk", "dairy", "cheese", "cream", "yogurt", "yoghurt", "buttermilk",
            "casein", "whey", "lactose"            
        ],
        "Egg": [
            "egg", "eggs", "egg white", "egg yolk", "albumin", "ovalbumin"
        ],
        "Fish": [
            "fish", "cod", "salmon", "tuna", "trout", "bass", "flounder", "anchovy",
            "anchovies", "snapper"
        ],
        "Crustaceans": [
            "crustacean", "crustaceans", "shrimp", "prawn", "prawns", "crab", "lobster",
            "crayfish", "krill"
        ],
        "Molluscs": [
            "mollusc", "mollusks", "oyster", "oysters", "mussel", "mussels", "clam",
            "clams", "scallop", "scallops", "squid", "octopus", "snail", "escargot"
        ],
        "Tree Nuts": [
            "almond", "hazelnut", "walnut", "cashew", "pecan", "pistachio", "macadamia",
            "brazil nut", "brazil nuts", "chestnut", "pine nut", "pine nuts"
        ],
        "Peanuts": [
            "peanut", "peanuts", "groundnut", "groundnuts", "arachis"
        ],
        "Soy": [
            "soy", "soya", "soybean", "soybeans", "edamame", "tofu", "tempeh", "miso",
            "natto", "tamari"
        ],
        "Sesame": [
            "sesame", "sesame seed", "sesame seeds", "tahini", "sesame oil"
        ],
        "Celery": [
            "celery", "celeriac", "celery salt"
        ],
        "Mustard": [
            "mustard", "mustard seed", "mustard seeds", "mustard powder", "dijon mustard"
        ],
        "Lupin": [
            "lupin", "lupine", "lupin flour"
        ],
        "Sulphites": [
            "sulphite", "sulphites", "sulfite", "sulfites", "sulfur dioxide",
            "sulphur dioxide", "metabisulfite", "metabisulphite"
        ]
    }

    output_filename = "../config/allergen_dict.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(allergen_dict, f, indent=4)
    
    print(f"Allergen dictionary saved to '{output_filename}'.")

if __name__ == "__main__":
    main()
