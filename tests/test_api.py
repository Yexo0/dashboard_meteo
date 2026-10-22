import requests

from src import api_client
from src.api_client import WeatherAPIClient
from src.data_processing import DataProcessor


def test_cache_write_then_read(tmp_path):
    client = WeatherAPIClient(db_path=str(tmp_path / "cache.db"))
    client._set_cached_data("paris", {"temperature": 20})
    assert client._get_cached_data("paris") == {"temperature": 20}


def test_cache_expired(tmp_path, monkeypatch):
    client = WeatherAPIClient(db_path=str(tmp_path / "cache.db"))
    client._set_cached_data("paris", {"temperature": 20})
    monkeypatch.setattr(api_client, "CACHE_TTL_MINUTES", 0)
    assert client._get_cached_data("paris") is None


def test_network_error_falls_back_to_mock(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise requests.exceptions.ConnectionError("pas de réseau")

    monkeypatch.setattr(requests, "get", no_network)
    client = WeatherAPIClient(db_path=str(tmp_path / "cache.db"))
    data = client.fetch_weather_and_air_quality(48.8566, 2.3522)
    assert "weather" in data and "air_quality" in data


def test_mock_data_gives_a_full_dataframe(tmp_path):
    client = WeatherAPIClient(db_path=str(tmp_path / "cache.db"))
    df = DataProcessor.process_raw_api_data(client._generate_mock_data(48.8566, 2.3522))
    assert len(df) == 24 * 7
    assert {"temperature_2m", "apparent_temperature", "us_aqi", "pm2_5"} <= set(df.columns)
