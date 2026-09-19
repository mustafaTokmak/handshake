from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")]
Scenario = Literal["accepted", "not_accepted", "pending", "unavailable"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateShipment(StrictModel):
    order_id: Identifier
    request_key: Identifier


class LookupRequest(StrictModel):
    request_key: Identifier


class GetShipment(StrictModel):
    shipment_id: Identifier


class Shipment(StrictModel):
    shipment_id: Identifier
    order_id: Identifier
    tracking_number: Identifier
    status: Literal["label_created"] = "label_created"


class ProviderResult(StrictModel):
    status: Literal["created", "pending", "not_accepted", "timeout", "unavailable", "expired", "key_mismatch", "not_found"]
    shipment: Shipment | None = None
    detail: str

    @model_validator(mode="after")
    def check_shipment(self):
        if (self.status == "created") != (self.shipment is not None):
            raise ValueError("Only created results contain a shipment")
        return self


class Outcome(StrictModel):
    status: Literal["completed", "unresolved"]
    shipment_id: Identifier | None = None
    tracking_number: Identifier | None = None
    explanation: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def check_completion(self):
        if self.status == "completed" and not (self.shipment_id and self.tracking_number):
            raise ValueError("Completion requires a shipment identifier and tracking number")
        if self.status == "unresolved" and (self.shipment_id or self.tracking_number):
            raise ValueError("Unresolved outcomes cannot claim shipment details")
        return self
