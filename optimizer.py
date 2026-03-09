import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from schemas import UtilityBill, Tariff, OptimizationRecommendation, RateComponent

class TariffOptimizer:
    """
    Analyzes historical consumption and compares it against regional tariffs 
    to find the most cost-effective plan.
    """
    def __init__(self, bill: UtilityBill):
        self.bill = bill
        # Assume billing period is monthly if not specified, used for annualization
        days = (bill.billing_period_end - bill.billing_period_start).days or 30
        self.period_days = max(days, 1)

    def simulate_cost(self, tariff: Tariff) -> float:
        """
        Simulates the cost of the current bill's consumption under a new tariff.
        Note: Simple simulation based on peak/off-peak totals.
        """
        total_cost = 0.0
        
        # We need to map our bill's peak/off-peak to the tariff's components.
        # This is a simplification. Real systems would use hourly intervals.
        for component in tariff.rates:
            if component.unit == "day":
                total_cost += component.rate * self.period_days
            elif component.unit == "kWh":
                if "peak" in component.name.lower():
                    total_cost += component.rate * self.bill.usage.peak_usage
                elif "off-peak" in component.name.lower() or "shoulder" in component.name.lower():
                    total_cost += component.rate * self.bill.usage.off_peak_usage
                else:
                    # If it's a flat rate or generic kWh rate, apply to total consumption
                    # (only if peak/off-peak weren't already handled by specific components)
                    # For simplicity: if the tariff doesn't split peak/off-peak, 
                    # we use total_consumption for the first kWh component we find.
                    if tariff.type == "Flat":
                        total_cost += component.rate * self.bill.usage.total_consumption
                        break
        
        return total_cost

    def get_recommendations(self, candidate_tariffs: List[Tariff]) -> List[OptimizationRecommendation]:
        results = []
        current_cost = self.bill.charges.total_amount
        
        for tariff in candidate_tariffs:
            simulated_cost = self.simulate_cost(tariff)
            # Add taxes/delivery if not explicitly in tariff (using current bill as baseline)
            # To be fair, we might just compare energy components or add full bill structure
            delivery = self.bill.charges.delivery_charges
            taxes = self.bill.charges.taxes
            projected_total = simulated_cost + delivery + taxes
            
            savings = current_cost - projected_total
            
            # Annualize
            annual_multiplier = 365 / self.period_days
            est_annual_cost = projected_total * annual_multiplier
            est_annual_savings = savings * annual_multiplier
            
            pros = []
            cons = []
            
            if savings > 0:
                pros.append(f"Save approximately ${savings:.2f} per month")
            if tariff.type == "TOU":
                pros.append("Rewards you for using power during off-peak hours")
                cons.append("Expensive during peak hours - monitor your heavy appliance usage")
            if any(r.unit == 'day' and r.rate > 0.5 for r in tariff.rates):
                cons.append("Higher daily fixed charge regardless of usage")
            
            if not pros:
                pros.append("Stable pricing")
            if not cons:
                cons.append("None identified")

            results.append(OptimizationRecommendation(
                tariff=tariff,
                estimated_annual_cost=round(est_annual_cost, 2),
                potential_savings=round(est_annual_savings, 2),
                rank=0, # Will sort later
                pros=pros,
                cons=cons,
                action_item=f"Contact {tariff.provider} to switch to the '{tariff.name}' plan."
            ))
            
        # Sort by savings descending
        results.sort(key=lambda x: x.potential_savings, reverse=True)
        for i, res in enumerate(results):
            res.rank = i + 1
            
        return results

class RegionalTariffScraper:
    """
    Mock API client for accessing regional electricity tariffs.
    In production, this would connect to URDB (US) or AER (Australia).
    """
    @staticmethod
    def get_tariffs(region: str) -> List[Tariff]:
        # Mock data for demonstration
        return [
            Tariff(
                tariff_id="T001",
                provider="EcoPower",
                name="Green Peak-Saver",
                type="TOU",
                rates=[
                    RateComponent(name="Peak (7am-10pm)", rate=0.22, unit="kWh", start_time="07:00", end_time="22:00"),
                    RateComponent(name="Off-Peak", rate=0.08, unit="kWh", start_time="22:00", end_time="07:00"),
                    RateComponent(name="Standing Charge", rate=0.45, unit="day")
                ],
                description="Optimized for households that shift usage to night time."
            ),
            Tariff(
                tariff_id="T002",
                provider="StandardGrid",
                name="Evergreen Flat",
                type="Flat",
                rates=[
                    RateComponent(name="Flat Rate", rate=0.18, unit="kWh"),
                    RateComponent(name="Standing Charge", rate=0.30, unit="day")
                ],
                description="Simple pricing with no time-of-use complexity."
            ),
            Tariff(
                tariff_id="T003",
                provider="NightOwl Energy",
                name="Ultra Low Night",
                type="TOU",
                rates=[
                    RateComponent(name="Peak", rate=0.35, unit="kWh"),
                    RateComponent(name="Off-Peak (12am-5am)", rate=0.04, unit="kWh"),
                    RateComponent(name="Standing Charge", rate=0.55, unit="day")
                ],
                description="Extreme savings if you charge EVs or run appliances overnight."
            )
        ]
