from typing import Dict, Any, List
import pandas as pd
import numpy as np


class DataProcessor:
    """
    Data Transformation, Calculations and Statistics.
    Author: Baptiste Dauvergne
    """

    @staticmethod
    def process_raw_api_data(raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Transforms raw API responses into a clean Pandas DataFrame."""
        w_hourly = raw_data.get("weather", {}).get("hourly", {})
        a_hourly = raw_data.get("air_quality", {}).get("hourly", {})

        df_weather = pd.DataFrame(w_hourly)
        df_air = pd.DataFrame(a_hourly)

        if df_weather.empty or df_air.empty:
            return pd.DataFrame()

        df = pd.merge(df_weather, df_air, on="time", how="inner")
        df["datetime"] = pd.to_datetime(df["time"])
        df.sort_values("datetime", inplace=True)
        return df

    @staticmethod
    def keep_past_hours(df: pd.DataFrame) -> pd.DataFrame:
        """
        The API also returns forecasts: keeps only past hours with complete data,
        so the last row is the current hour.
        """
        if df.empty:
            return df
        return df[df["datetime"] <= pd.Timestamp.now()].dropna()

    @staticmethod
    def calculate_custom_health_index(df: pd.DataFrame) -> pd.Series:
        """
        Calculates a custom composite Comfort/Health Score (0-100 scale).
        Higher is better.
        """
        temp = df["apparent_temperature"]
        humidity = df["relativehumidity_2m"]
        pm2_5 = df["pm2_5"]

        # Penalty factors based on optimal comfort conditions
        temp_penalty = np.abs(temp - 21.0) * 1.5
        humidity_penalty = np.abs(humidity - 50.0) * 0.3
        pollution_penalty = pm2_5 * 1.2

        score = 100 - (temp_penalty + humidity_penalty + pollution_penalty)
        return score.clip(0, 100).round(1)

    @staticmethod
    def compute_statistics(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Mean / median over the last 24h and 7 days, and trends
        (latest value minus the value 24h / 7 days before).
        """
        latest_time = df["datetime"].iloc[-1]
        last_24h = df[df["datetime"] >= latest_time - pd.Timedelta(hours=24)]
        last_7d = df[df["datetime"] >= latest_time - pd.Timedelta(days=7)]

        stats = {}
        for col in columns:
            stats[col] = {
                "Moyenne 24h": last_24h[col].mean(),
                "Médiane 24h": last_24h[col].median(),
                "Moyenne 7j": last_7d[col].mean(),
                "Médiane 7j": last_7d[col].median(),
                "Tendance 24h": last_24h[col].iloc[-1] - last_24h[col].iloc[0],
                "Tendance 7j": last_7d[col].iloc[-1] - last_7d[col].iloc[0],
            }
        return pd.DataFrame(stats).T.round(1)

    @staticmethod
    def get_aqi_category(aqi: float) -> str:
        """Returns the US AQI category of a value."""
        if aqi <= 50:
            return "Bon"
        if aqi <= 100:
            return "Modéré"
        if aqi <= 150:
            return "Mauvais pour les sensibles"
        if aqi <= 200:
            return "Mauvais"
        if aqi <= 300:
            return "Très mauvais"
        return "Dangereux"
