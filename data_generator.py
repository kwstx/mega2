import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_historical_data(days=30):
    """
    Generates synthetic hourly electricity prices and weather data.
    Prices are influenced by:
    - Hour of day (Peak at 8am and 6pm)
    - Temperature (Higher prices in extremes)
    - Random noise
    """
    start_date = datetime.now() - timedelta(days=days)
    data = []
    
    for i in range(days * 24):
        current_time = start_date + timedelta(hours=i)
        hour = current_time.hour
        day_of_week = current_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Base temperature: sine wave over 24h + seasonal trend
        base_temp = 15 + 10 * np.sin(2 * np.pi * (hour - 14) / 24)
        temp = base_temp + np.random.normal(0, 2)
        
        # Base price logic ($/kWh)
        # Higher in morning (7-9) and evening (17-21)
        if 7 <= hour <= 10:
            price_factor = 2.5
        elif 17 <= hour <= 21:
            price_factor = 3.0
        elif 0 <= hour <= 5:
            price_factor = 0.5
        else:
            price_factor = 1.0
            
        # Temperature impact: extreme cold/heat increases demand
        temp_impact = 1.0 + (abs(temp - 20) / 40)
        
        # Base price (cents per kWh)
        base_price = 15.0 
        price = base_price * price_factor * temp_impact + np.random.normal(0, 1)
        
        data.append({
            "timestamp": current_time,
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "temperature": round(temp, 1),
            "price": round(max(2, price), 2) # Min price 2 cents
        })
        
    df = pd.DataFrame(data)
    df.to_csv("historical_prices.csv", index=False)
    print(f"Generated {len(df)} rows of historical data.")
    return df

def generate_forecast_weather(hours=48):
    """Generates synthetic weather forecast for the next 48 hours."""
    start_time = datetime.now()
    data = []
    
    for i in range(hours):
        current_time = start_time + timedelta(hours=i)
        hour = current_time.hour
        base_temp = 15 + 10 * np.sin(2 * np.pi * (hour - 14) / 24)
        temp = base_temp + np.random.normal(0, 1)
        
        data.append({
            "timestamp": current_time,
            "hour": hour,
            "day_of_week": current_time.weekday(),
            "is_weekend": 1 if current_time.weekday() >= 5 else 0,
            "temperature": round(temp, 1)
        })
        
    df = pd.DataFrame(data)
    df.to_csv("weather_forecast.csv", index=False)
    print(f"Generated {len(df)} rows of weather forecast.")
    return df

if __name__ == "__main__":
    generate_historical_data()
    generate_forecast_weather()
