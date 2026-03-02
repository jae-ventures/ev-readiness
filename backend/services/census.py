import httpx
from config import CENSUS_API_KEY

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# Median income thresholds for scoring
# Based on Georgia median household income (~$65k)
INCOME_THRESHOLDS = {
    "high":   80000,   # above this → score 1.0
    "low":    30000,   # below this → score 0.0
}


async def get_tract_for_coordinate(lat: float, lon: float) -> dict | None:
    """
    Convert a lat/lon to Census tract identifiers using the Census geocoder.
    Returns dict with state, county, tract FIPS codes, or None if not found.
    """
    params = {
        "x": lon,           # Census geocoder uses x for longitude
        "y": lat,           # and y for latitude
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "Census Tracts",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(GEOCODER_URL, params=params)
        response.raise_for_status()
        data = response.json()

    try:
        result = data["result"]
        geographies = result["geographies"]["Census Tracts"][0]
        return {
            "state": geographies["STATE"],
            "county": geographies["COUNTY"],
            "tract": geographies["TRACT"],
        }
    except (KeyError, IndexError):
        return None


async def get_acs_data(state: str, county: str, tract: str) -> dict | None:
    """
    Fetch ACS 5-year estimates for a specific census tract.
    Returns raw ACS values or None if unavailable.
    """
    params = {
        "get": "B25003_001E,B25003_002E,B25003_003E,B19013_001E",
        "for": f"tract:{tract}",
        "in": f"state:{state} county:{county}",
        "key": CENSUS_API_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(ACS_URL, params=params)
        response.raise_for_status()
        data = response.json()

    # ACS returns a 2D array — first row is headers, second is values
    if len(data) < 2:
        return None

    headers = data[0]
    values = data[1]
    return dict(zip(headers, values))


def score_housing_type(acs_data: dict) -> float:
    """
    Pure function. Scores based on renter vs owner occupancy.

    Higher renter percentage = lower score because renters face
    more barriers to EV charging (can't install home chargers).
    This is the core equity insight of the application.
    """
    try:
        total = int(acs_data.get("B25003_001E", 0))
        renters = int(acs_data.get("B25003_003E", 0))
    except (ValueError, TypeError):
        return 0.5  # neutral fallback if data is missing

    if total == 0:
        return 0.5

    renter_rate = renters / total

    # Invert: high renter rate = low score
    # 100% renters → 0.0, 0% renters → 1.0
    return round(1.0 - renter_rate, 3)


def score_income_affordability(acs_data: dict) -> float:
    """
    Pure function. Scores based on median household income.
    Higher income = higher score (more EV purchase feasibility).
    Normalized between defined low and high thresholds.
    """
    try:
        income = int(acs_data.get("B19013_001E", -1))
    except (ValueError, TypeError):
        return 0.5

    # -666666666 is Census's code for missing/unavailable data
    if income < 0:
        return 0.5

    low = INCOME_THRESHOLDS["low"]
    high = INCOME_THRESHOLDS["high"]

    # Clamp and normalize to 0.0-1.0
    clamped = max(low, min(income, high))
    return round((clamped - low) / (high - low), 3)


async def fetch_census_data(lat: float, lon: float) -> dict | None:
    """
    Orchestrates the two-step Census lookup.
    Returns combined ACS data dict, or None if either step fails.
    """
    tract_info = await get_tract_for_coordinate(lat, lon)
    if not tract_info:
        return None

    return await get_acs_data(
        tract_info["state"],
        tract_info["county"],
        tract_info["tract"]
    )