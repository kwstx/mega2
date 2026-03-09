import os
from parser import BillParser
from optimizer import TariffOptimizer, RegionalTariffScraper

def run_optimization_demo():
    print("=== Electricity Bill Optimizer Demo ===\n")
    
    # 1. Load and Parse Current Bill
    parser = BillParser()
    bill_path = "test_bill.csv"
    
    if not os.path.exists(bill_path):
        print(f"Error: {bill_path} not found.")
        return

    with open(bill_path, "rb") as f:
        content = f.read()
        
    result = parser.parse_csv(content)
    
    if not result.success:
        print(f"Failed to parse bill: {result.errors}")
        return
    
    bill = result.data
    print(f"Current Bill: {bill.provider} - ${bill.charges.total_amount:.2f}")
    print(f"Usage: {bill.usage.total_consumption} kWh (Peak: {bill.usage.peak_usage}, Off-Peak: {bill.usage.off_peak_usage})")
    print("-" * 40)

    # 2. Fetch Regional Tariffs
    print("Fetching regional tariffs for early adopters...")
    tariffs = RegionalTariffScraper.get_tariffs("REGION_XYZ")
    print(f"Found {len(tariffs)} available plans.\n")

    # 3. Analyze and Recommend
    optimizer = TariffOptimizer(bill)
    recommendations = optimizer.get_recommendations(tariffs)

    print("=== TOP RECOMMENDATIONS ===")
    for rec in recommendations:
        saving_tag = f"[SAVINGS: ${rec.potential_savings}/yr]" if rec.potential_savings > 0 else "[COST INCREASE]"
        print(f"{rec.rank}. {rec.tariff.provider} - {rec.tariff.name} {saving_tag}")
        print(f"   Est. Annual Cost: ${rec.estimated_annual_cost:.2f}")
        print(f"   Pros: {', '.join(rec.pros)}")
        print(f"   Action: {rec.action_item}")
        print()

if __name__ == "__main__":
    run_optimization_demo()
