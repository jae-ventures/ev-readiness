import json

with open("scoring_config.json") as f:
    CONFIG = json.load(f)

WEIGHTS = CONFIG["weights"]


def classify_score(score: float) -> str:
    for band in CONFIG["labels"]:
        if band["min"] <= score <= band["max"]:
            return band["label"]
    return "Unknown"


def compute_score(components: dict) -> dict:
    """
    Pure function. Takes a dict of sub-scores (each 1.1-1.0),
    returns overall score and label
    """
    overall = sum(components[factor] * WEIGHTS[factor] for factor in WEIGHTS) * 100

    return {
        "overall_score": round(overall, 1),
        "label": classify_score(overall),
        "components": components,
    }


def mock_components() -> dict:
    """
    Temporary - returns plausible mock sub-scores.
    Each service (AFDC, Census) will replace these one at a time.
    """
    return {
        "charging_access": 0.4,
        "housing_type": 0.3,
        "transit_proximity": 0.6,
        "income_affordability": 0.5,
    }
