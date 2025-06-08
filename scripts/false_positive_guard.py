#!/usr/bin/env python
"""
false_positive_guard.py
-----------------------

Return **True**  →  skip / ignore the match  
Return **False** →  keep the match
"""

from __future__ import annotations
import re


_NON_DAIRY_MILK = re.compile(
    r"\b(?:coconut|almond|oat|rice|soy|hemp|cashew|pea)\s+milk\b", re.I
)
_VEGAN_BUTTER   = re.compile(r"\bvegan\s+butter\b", re.I)
_COCOA_BUTTER   = re.compile(r"\bcocoa\s+butter\b", re.I)


_EGG_REPLACER   = re.compile(
    r"\b(?:egg\s+replacer|vegan\s+egg|plant[-\s]based\s+egg)\b", re.I
)
_VEGAN_MAYO     = re.compile(r"\bvegan\s+mayonnaise\b", re.I)


_GLUTEN_FREE    = re.compile(r"\bgluten[-\s]?free\b", re.I)
_ALT_FLOUR      = re.compile(
    r"\b(?:rice|almond|oat|coconut|soy|corn|buckwheat|cassava|garbanzo|"
    r"chickpea|quinoa)\s+flour\b",
    re.I,
)


def is_false_positive(allergen: str, ingredient: str) -> bool:
    """Return *True* if the match should be discarded."""
    txt = ingredient.lower()

    if allergen == "Milk":
        if _NON_DAIRY_MILK.search(txt) or _VEGAN_BUTTER.search(txt) or _COCOA_BUTTER.search(txt):
            return True

    elif allergen == "Egg":
        if _EGG_REPLACER.search(txt) or _VEGAN_MAYO.search(txt):
            return True

    elif allergen == "Gluten":
        if _GLUTEN_FREE.search(txt) or _ALT_FLOUR.search(txt):
            return True

    return False
