import pandas as pd
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
from schemas import DeviceConfig, SchedulingConstraints, ScheduleSlot, ScheduleResponse

class SmartScheduler:
    """
    Advanced scheduler that optimizes device usage based on electricity prices,
    user constraints, and manual overrides.
    """
    def __init__(self, device: DeviceConfig, constraints: SchedulingConstraints):
        self.device = device
        self.constraints = constraints
        self.manual_override = False

    def get_schedule(self, predictions_df: pd.DataFrame, manual_override: bool = False) -> ScheduleResponse:
        self.manual_override = manual_override
        
        now = datetime.now()
        # Parse ready_by_time
        ready_hour, ready_min = map(int, self.constraints.ready_by_time.split(":"))
        ready_by = now.replace(hour=ready_hour, minute=ready_min, second=0, microsecond=0)
        
        # If ready_by is in the past today, set it for tomorrow
        if ready_by <= now:
            ready_by += timedelta(days=1)

        # Filter predictions until ready_by
        # Convert timestamp strings to datetime if they aren't already
        if not pd.api.types.is_datetime64_any_dtype(predictions_df['timestamp']):
            predictions_df['timestamp'] = pd.to_datetime(predictions_df['timestamp'])
            
        window = predictions_df[predictions_df['timestamp'] < ready_by].copy()
        
        # Calculate hours needed to fulfill energy requirement
        # energy (kWh) / power (kW) = time (h)
        hours_needed = self.device.energy_needed_kwh / self.device.power_rate_kw
        num_slots = int(hours_needed) + (1 if hours_needed % 1 > 0 else 0)

        if manual_override:
            # Manual override: just pick the next N slots starting from now
            # (Safety: build trust by allowing user to force-start)
            charging_slots = window.head(num_slots).copy()
            status = "Override (Charging)"
        else:
            # Shift usage to lower-cost periods
            # Sort window by price
            sorted_window = window.sort_values(by="predicted_price")
            charging_slots = sorted_window.head(num_slots).copy()
            status = "Optimizing"

        # Prepare slots for response
        all_slots = []
        total_cost = 0.0
        
        # Mark which slots are active
        active_timestamps = set(charging_slots['timestamp'])
        
        for _, row in window.iterrows():
            is_active = row['timestamp'] in active_timestamps
            all_slots.append(ScheduleSlot(
                timestamp=row['timestamp'],
                price=row['predicted_price'],
                is_active=is_active
            ))
            if is_active:
                # Approximate cost: (energy / num_slots) * (price / 100)
                energy_per_slot = self.device.energy_needed_kwh / num_slots
                total_cost += (energy_per_slot * row['predicted_price']) / 100

        # Calculate "Dumb" cost for savings comparison
        dumb_slots = window.head(num_slots)
        dumb_cost = (dumb_slots['predicted_price'] * (self.device.energy_needed_kwh / num_slots)).sum() / 100
        savings = dumb_cost - total_cost

        return ScheduleResponse(
            device_id=self.device.id,
            slots=all_slots,
            total_cost=round(total_cost, 2),
            savings=round(max(0, savings), 2),
            ready_by=self.constraints.ready_by_time,
            manual_override=self.manual_override,
            status=status
        )

if __name__ == "__main__":
    # Test logic
    from predictor import PricePredictor
    predictor = PricePredictor()
    prices = predictor.predict()
    
    device = DeviceConfig(id="EV-123", name="Tesla Model 3", energy_needed_kwh=40)
    constraints = SchedulingConstraints(ready_by_time="07:00")
    
    scheduler = SmartScheduler(device, constraints)
    print("Normal Optimization:")
    print(scheduler.get_schedule(prices).json())
    
    print("\nManual Override:")
    print(scheduler.get_schedule(prices, manual_override=True).json())
