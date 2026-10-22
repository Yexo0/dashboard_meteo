from typing import Dict, List
import pandas as pd

# Thresholds for alerts (WHO Guidelines)
THRESHOLDS = {
    "pm2_5": {"warning": 15.0, "danger": 25.0, "unit": "µg/m³"},
    "pm10": {"warning": 45.0, "danger": 50.0, "unit": "µg/m³"},
    "no2": {"warning": 25.0, "danger": 50.0, "unit": "µg/m³"},
    "temp_max": {"warning": 33.0, "danger": 38.0, "unit": "°C"}
}


def detect_alerts(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Scans the latest data point for threshold violations.
    Author: Student B (Data Analyst)
    """
    alerts = []
    if df.empty:
        return alerts

    latest = df.iloc[-1]

    # PM2.5 check
    if latest["pm2_5"] >= THRESHOLDS["pm2_5"]["danger"]:
        alerts.append({
            "level": "danger",
            "message": f"Alerte Rouge Pollution (PM2.5) : {latest['pm2_5']:.1f} {THRESHOLDS['pm2_5']['unit']} (Seuil: {THRESHOLDS['pm2_5']['danger']})"
        })
    elif latest["pm2_5"] >= THRESHOLDS["pm2_5"]["warning"]:
        alerts.append({
            "level": "warning",
            "message": f"Vigilance Pollution (PM2.5) : {latest['pm2_5']:.1f} {THRESHOLDS['pm2_5']['unit']}"
        })

    # PM10 check
    if latest["pm10"] >= THRESHOLDS["pm10"]["danger"]:
        alerts.append({
            "level": "danger",
            "message": f"Alerte Rouge Pollution (PM10) : {latest['pm10']:.1f} {THRESHOLDS['pm10']['unit']} (Seuil: {THRESHOLDS['pm10']['danger']})"
        })
    elif latest["pm10"] >= THRESHOLDS["pm10"]["warning"]:
        alerts.append({
            "level": "warning",
            "message": f"Vigilance Pollution (PM10) : {latest['pm10']:.1f} {THRESHOLDS['pm10']['unit']}"
        })

    # NO2 check
    if latest["nitrogen_dioxide"] >= THRESHOLDS["no2"]["danger"]:
        alerts.append({
            "level": "danger",
            "message": f"Alerte Pic de Pollution NO2 : {latest['nitrogen_dioxide']:.1f} {THRESHOLDS['no2']['unit']}"
        })
    elif latest["nitrogen_dioxide"] >= THRESHOLDS["no2"]["warning"]:
        alerts.append({
            "level": "warning",
            "message": f"Vigilance NO2 : {latest['nitrogen_dioxide']:.1f} {THRESHOLDS['no2']['unit']}"
        })

    # Temperature check
    if latest["temperature_2m"] >= THRESHOLDS["temp_max"]["danger"]:
        alerts.append({
            "level": "danger",
            "message": f"Alerte Canicule : {latest['temperature_2m']:.1f} °C"
        })
    elif latest["temperature_2m"] >= THRESHOLDS["temp_max"]["warning"]:
        alerts.append({
            "level": "warning",
            "message": f"Vigilance Forte Chaleur : {latest['temperature_2m']:.1f} °C"
        })

    return alerts
