from pydantic import BaseModel

class LocationRequest(BaseModel):
    lat: float
    lon: float
    address: str | None = None

class ScoreComponents(BaseModel):
    charging_access: float
    housing_type: float
    transit_proximity: float
    income_affordability: float

class ReadinessResponse(BaseModel):
    lat: float
    lon: float
    overall_score: float
    label: str
    components: ScoreComponents