import pandas as pd

from src.data_processing import DataProcessor
from src.alerts import detect_alerts


def make_df():
    return pd.DataFrame({
        "datetime": pd.to_datetime(["2026-01-01T00:00", "2026-01-01T01:00"]),
        "temperature_2m": [21.0, 40.0],
        "apparent_temperature": [21.0, 43.0],
        "relativehumidity_2m": [50.0, 20.0],
        "pm2_5": [10.0, 30.0],
        "pm10": [20.0, 55.0],
        "nitrogen_dioxide": [15.0, 60.0]
    })


def test_health_index_calculation():
    scores = DataProcessor.calculate_custom_health_index(make_df())
    assert len(scores) == 2
    assert scores.iloc[0] > scores.iloc[1]
    assert scores.between(0, 100).all()


def test_alerts_detection():
    messages = [alert["message"] for alert in detect_alerts(make_df())]
    assert len(messages) == 4
    assert any("Canicule" in message for message in messages)


def test_no_alert_when_values_are_ok():
    assert detect_alerts(make_df().head(1)) == []


def test_keep_past_hours_removes_forecasts_and_missing_values():
    now = pd.Timestamp.now()
    df = pd.DataFrame({
        "datetime": [now - pd.Timedelta(hours=2), now - pd.Timedelta(hours=1), now + pd.Timedelta(hours=5)],
        "us_aqi": [30.0, None, 40.0]
    })
    past = DataProcessor.keep_past_hours(df)
    assert len(past) == 1
    assert past["us_aqi"].iloc[-1] == 30.0


def test_statistics_and_trends():
    df = pd.DataFrame({
        "datetime": pd.date_range("2026-01-01", periods=8 * 24, freq="h"),
        "temperature_2m": [float(i) for i in range(8 * 24)]
    })
    stats = DataProcessor.compute_statistics(df, ["temperature_2m"])
    assert stats.loc["temperature_2m", "Tendance 24h"] == 24
    assert stats.loc["temperature_2m", "Tendance 7j"] == 168
    assert stats.loc["temperature_2m", "Moyenne 24h"] == 179


def test_aqi_category():
    assert DataProcessor.get_aqi_category(20) == "Bon"
    assert DataProcessor.get_aqi_category(75) == "Modéré"
    assert DataProcessor.get_aqi_category(350) == "Dangereux"
