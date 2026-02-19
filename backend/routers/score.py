from fastapi import APIRouter

from models.schemas import ReadinessResponse
from services.scoring import compute_score, mock_components

router = APIRouter()


@router.get("/score", response_model=ReadinessResponse)
async def get_score(lat: float, lon: float):
    components = mock_components()
    result = compute_score(components)

    return ReadinessResponse(lat=lat, lon=lon, **result)
