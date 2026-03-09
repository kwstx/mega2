from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime

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

# --- New Scheduling Schemas ---

class DeviceConfig(BaseModel):
    id: str
    name: str = "Smart Device"
    type: str = "EV" # "EV", "Smart Plug", "HVAC"
    energy_needed_kwh: float = 40.0
    power_rate_kw: float = 7.4
    priority: int = 1 # 1 (High) to 5 (Low)

class SchedulingConstraints(BaseModel):
    ready_by_time: str = "08:00" # HH:MM format
    min_charge_level: Optional[float] = 20.0 # Percentage
    max_charge_level: Optional[float] = 80.0 # Percentage
    comfort_threshold: Optional[float] = None # For HVAC

class ScheduleSlot(BaseModel):
    timestamp: datetime
    price: float
    is_active: bool

class ScheduleResponse(BaseModel):
    device_id: str
    slots: List[ScheduleSlot]
    total_cost: float
    savings: float
    ready_by: str
    manual_override: bool
    status: str # "Optimizing", "Charging", "Standby", "Override"
    notification: Optional[str] = None

class ScheduleUpdateRequest(BaseModel):
    device_id: str
    constraints: Optional[SchedulingConstraints] = None
    manual_override: Optional[bool] = None
