from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Order(StrictModel):
    reference: str = Field(default="ORDER-2048", pattern=r"^ORDER-[A-Z0-9-]{1,40}$")
    weight_kg: float = Field(default=2.4, gt=0, le=50)
    distance_km: int = Field(default=330, ge=1, le=2500)
    destination_country: Literal["GB"] = "GB"


class Quote(StrictModel):
    amount_minor: int = Field(strict=True, gt=0, le=1000000)
    currency: Literal["GBP"]
    eta_days: int = Field(strict=True, ge=1, le=30)
    service: str = Field(min_length=1, max_length=80)


class Candidate(StrictModel):
    hypothesis: str = Field(min_length=10, max_length=1500)
    source: str = Field(min_length=40, max_length=16000)
    evidence: list[str] = Field(default_factory=list, max_length=10)


class StartRequest(StrictModel):
    order: Order = Field(default_factory=Order)
    condition: Literal["baseline", "optimized", "protected"] = "baseline"
    attack: bool = True


class ContactReply(StrictModel):
    message_id: str = Field(min_length=1, max_length=100)
    context: str = Field(min_length=10, max_length=12000)
    source: str = Field(default="carrier-contact-agent", min_length=1, max_length=100)
