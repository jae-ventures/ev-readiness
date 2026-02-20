from fastapi import APIRouter, HTTPException
from models.schemas import ReadinessResponse
from services.afdc import fetch_nearby_stations, score_charging_access
from services.scoring import compute_score, mock_components

router = APIRouter()


@router.get("/score", response_model=ReadinessResponse)
async def get_score(lat: float, lon: float):
    try:
        stations = await fetch_nearby_stations(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AFDC API error: {str(e)}")

    # Start with mocks, override with real data as each service is wired in
    components = mock_components()
    components["charging_access"] = score_charging_access(stations)

    result = compute_score(components)

    return ReadinessResponse(lat=lat, lon=lon, **result)


@router.get("/debug/stations")
async def debug_stations(lat: float, lon: float, radius: float = 1.0):
    stations = await fetch_nearby_stations(lat, lon, radius)
    return {
        "count": len(stations),
        "stations": [
            {
                "name": s.get("station_name"),
                "city": s.get("city"),
                "l2_ports": s.get("ev_level2_evse_num"),
                "dcfc_ports": s.get("ev_dc_fast_num"),
                "access": s.get("access_code"),
            }
            for s in stations
        ],
    }
