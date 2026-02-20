import httpx

from config import AFDC_API_KEY

AFDC_NEAREST_BASE = "https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json"


async def fetch_nearby_stations(
    lat: float, lon: float, radius_miles: float = 1.0
) -> list[dict]:
    """
    Fetch EV charging stations within radius_miles of a coordinate.
    Uses the /nearest endpoint which supports lat/lon + radius filtering.
    Returns raw station list from AFDC.
    """
    params = {
        "api_key": AFDC_API_KEY,
        "fuel_type": "ELEC",
        # "zip": 30308,
        "latitude": lat,
        "longitude": lon,
        "radius": radius_miles,
        "limit": 50,
        "status": "E",
        "ev_connector_type": "J1772,J1772COMBO,TESLA",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(AFDC_NEAREST_BASE, params=params)
        response.raise_for_status()
        data = response.json()

    return data.get("fuel_stations", [])


def score_charging_access(stations: list[dict]) -> float:
    """
    Pure function. Takes a list of AFDC station dicts,
    returns a 0.0-1.0 sub-score.

    Scoring logic:
    - Count of stations within radius (quantity)
    - Level 3/DCFC chargers weighted more heavily than L2 (Might be wise to consider destination L2/DCFC chargers with higher weight)
    - Caps out at 1.0
    """
    if not stations:
        return 0.0

    score = 0.0

    for station in stations:
        level = station.get("ev_level2_evse_num") or 0
        dcfc = station.get("ev_dc_fast_num") or 0

        score += level * 0.05  # each L2 port adds 0.05
        score += dcfc * 0.15  # each DCFC port adds 0.15
        # TODO: In the future we can consider proximity to relevant locations

    return min(score, 1.0)
