import pandas as pd
from datetime import datetime, timedelta

class EVAssetManager:
    """
    Optimizes EV charging based on predicted electricity prices.
    """
    def __init__(self, energy_required_kwh=40, charge_rate_kw=7.4, target_hour=8):
        self.energy_required_kwh = energy_required_kwh
        self.charge_rate_kw = charge_rate_kw  # Typical Level 2 charger
        self.target_hour = target_hour # Target completion hour (e.g., 8 AM)
        
    def optimize_charging(self, predictions_df):
        """
        Identifies the cheapest hours to charge the EV to meet the requirement.
        """
        # Filter for the next 24 hours (or until target hour)
        now = datetime.now()
        # For simplicity, we assume we finish by the next occurrence of target_hour
        # If it's currently past target_hour, we look at the next day
        
        # Calculate hours needed
        hours_needed = int(self.energy_required_kwh / self.charge_rate_kw) + 1
        
        # Sort predictions by price
        # We only consider the next available window (e.g., next 24h)
        window = predictions_df.head(24).copy()
        window = window.sort_values(by="predicted_price")
        
        # Pick the N cheapest hours
        charging_hours = window.head(hours_needed)
        charging_hours = charging_hours.sort_values(by="timestamp")
        
        # Calculate cost
        optimized_cost = (charging_hours['predicted_price'] * (self.energy_required_kwh / hours_needed)).sum() / 100 # convert cents to dollars
        
        # Calculate "Dumb" cost (charging immediately)
        dumb_charging = predictions_df.head(hours_needed)
        dumb_cost = (dumb_charging['predicted_price'] * (self.energy_required_kwh / hours_needed)).sum() / 100
        
        savings = dumb_cost - optimized_cost
        
        return {
            "charging_schedule": charging_hours[['timestamp', 'predicted_price']].to_dict(orient="records"),
            "optimized_cost": round(optimized_cost, 2),
            "dumb_cost": round(dumb_cost, 2),
            "savings": round(max(0, savings), 2),
            "hours_needed": hours_needed
        }

if __name__ == "__main__":
    from predictor import PricePredictor
    predictor = PricePredictor()
    results = predictor.predict()
    if results is not None:
        mgr = EVAssetManager()
        plan = mgr.optimize_charging(results)
        print("Optimization Plan:")
        print(f"Cost with optimization: ${plan['optimized_cost']}")
        print(f"Cost without optimization: ${plan['dumb_cost']}")
        print(f"Savings: ${plan['savings']}")
