import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import pickle
import os

class PricePredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_path = "price_model.pkl"
        
    def train(self, data_path="historical_prices.csv"):
        if not os.path.exists(data_path):
            print("Historical data not found. Please run data_generator.py first.")
            return
            
        df = pd.read_csv(data_path)
        
        # Features: hour, day_of_week, is_weekend, temperature
        X = df[['hour', 'day_of_week', 'is_weekend', 'temperature']]
        y = df['price']
        
        self.model.fit(X, y)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print("Model trained and saved.")

    def predict(self, forecast_path="weather_forecast.csv"):
        if not os.path.exists(self.model_path):
            self.train()
            
        if not os.path.exists(forecast_path):
            print("Weather forecast not found.")
            return None
            
        df_forecast = pd.read_csv(forecast_path)
        X_forecast = df_forecast[['hour', 'day_of_week', 'is_weekend', 'temperature']]
        
        predictions = self.model.predict(X_forecast)
        df_forecast['predicted_price'] = predictions
        
        return df_forecast

if __name__ == "__main__":
    predictor = PricePredictor()
    predictor.train()
    results = predictor.predict()
    if results is not None:
        print("Sample predictions:")
        print(results[['timestamp', 'predicted_price']].head())
