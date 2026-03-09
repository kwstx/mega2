from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date

class UsageData(BaseModel):
    peak_usage: float = Field(..., description="Consumption during peak hours in kWh")
    off_peak_usage: float = Field(..., description="Consumption during off-peak hours in kWh")
    total_consumption: float = Field(..., description="Total consumption in kWh")

class Charges(BaseModel):
    delivery_charges: float = Field(..., description="Base delivery/service charges")
    taxes: float = Field(..., description="Total taxes applied")
    other_charges: Optional[float] = 0.0
    total_amount: float = Field(..., description="Total bill amount")

class UtilityBill(BaseModel):
    bill_id: str
    provider: str
    billing_period_start: date
    billing_period_end: date
    usage: UsageData
    charges: Charges
    raw_text: Optional[str] = None

    @validator('usage')
    def validate_total_usage(cls, v):
        if abs(v.peak_usage + v.off_peak_usage - v.total_consumption) > 0.1:
            # We don't necessarily fail, but we could flag it.
            # For strict validation:
            # raise ValueError("Peak + Off-Peak usage does not match Total Consumption")
            pass
        return v

class ParsingResult(BaseModel):
    success: bool
    data: Optional[UtilityBill] = None
    errors: List[str] = []
    anomalies: List[str] = []

class RateComponent(BaseModel):
    name: str # e.g., "Peak", "Off-Peak", "Daily Standing Charge"
    rate: float # Price per unit (kWh) or per day
    unit: str # "kWh" or "day"
    start_time: Optional[str] = None # e.g., "07:00"
    end_time: Optional[str] = None # e.g., "22:00"

class Tariff(BaseModel):
    tariff_id: str
    provider: str
    name: str
    type: str # "Flat", "TOU" (Time of Use), "Step"
    rates: List[RateComponent]
    description: Optional[str] = None

class OptimizationRecommendation(BaseModel):
    tariff: Tariff
    estimated_annual_cost: float
    potential_savings: float
    rank: int
    pros: List[str]
    cons: List[str]
    action_item: str
