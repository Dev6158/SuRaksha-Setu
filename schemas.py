from pydantic import BaseModel, Field
from typing import List


class TelemetryFrame(BaseModel):

    swipe_speed: float = Field(..., ge=0)
    tap_force: float = Field(..., ge=0)

    gyro_x: float
    gyro_y: float
    gyro_z: float

    latitude: float
    longitude: float


class ForensicAnalysisResponse(BaseModel):

    ela_score: float
    fft_score: float

    anomaly_detected: bool

    anomaly_regions: List[str]

    confidence_score: float


class RiskScorePayload(BaseModel):

    risk_score: float = Field(..., ge=0, le=100)

    risk_level: str

    fraud_codes: List[str]

    explanation: str