import logging
import pandas as pd
import plotly.express as px
import streamlit as st

from src.api_client import WeatherAPIClient
from src.data_processing import DataProcessor
from src.alerts import detect_alerts

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_CITIES = {
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Lyon": {"lat": 45.7640, "lon": 4.8357},
    "Marseille": {"lat": 43.2965, "lon": 5.3698},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Madrid": {"lat": 40.4168, "lon": -3.7038}
}

# Map colors for each US AQI category
AQI_COLORS = {
    "Bon": "green",
    "Modéré": "gold",
    "Mauvais pour les sensibles": "orange",
    "Mauvais": "red",
    "Très mauvais": "purple",
    "Dangereux": "maroon"
}


def render_dashboard():
    """
    Renders Streamlit Web Application Interface.
    Author: Student C (Lead UI/UX)
    """
    st.set_page_config(page_title="Dashboard Météo & AQI", page_icon="🌤️", layout="wide")

    st.title("🌤️ Dashboard Météo & Surveillance Qualité de l'Air")
    st.markdown("Projet 3ᵉ Année Ingénieur — Analyse de données environnementales en temps réel")

    client = WeatherAPIClient()

    # Sidebar Options
    st.sidebar.header("⚙️ Configuration")
    selected_city = st.sidebar.selectbox("Sélectionner une ville", list(DEFAULT_CITIES.keys()))
    mock_mode = st.sidebar.checkbox("Mode Déconnecté / Data Mocked", value=False)

    city_info = DEFAULT_CITIES[selected_city]

    # Fetch Data for every city (needed for the map)
    with st.spinner("Chargement des données des villes..."):
        all_data = {}
        for city, coords in DEFAULT_CITIES.items():
            raw_data = client.fetch_weather_and_air_quality(coords["lat"], coords["lon"], mock_mode=mock_mode)
            all_data[city] = DataProcessor.process_raw_api_data(raw_data)
        df = all_data[selected_city]

    if df.empty:
        st.error("Impossible de récupérer ou d'afficher les données.")
        return

    # Add calculated metrics
    df["health_score"] = DataProcessor.calculate_custom_health_index(df)
    df_past = DataProcessor.keep_past_hours(df)
    if df_past.empty:
        st.error("Pas encore de mesures disponibles pour cette ville.")
        return
    latest = df_past.iloc[-1]

    # Period and metrics selection
    first_day = df["datetime"].min().date()
    last_day = df["datetime"].max().date()
    start_day, end_day = st.sidebar.slider(
        "Période affichée", min_value=first_day, max_value=last_day,
        value=(first_day, last_day), format="DD/MM"
    )
    metric_options = [col for col in df.columns if col not in ("time", "datetime")]
    selected_metrics = st.sidebar.multiselect(
        "Métriques à afficher", metric_options,
        default=["temperature_2m", "relativehumidity_2m", "us_aqi"]
    )
    df_period = df[(df["datetime"].dt.date >= start_day) & (df["datetime"].dt.date <= end_day)]

    # Alert Box Section
    alerts = detect_alerts(df_past)
    if alerts:
        for alert in alerts:
            if alert["level"] == "danger":
                st.error(f"🚨 **DANGER** : {alert['message']}")
            else:
                st.warning(f"⚠️ **ATTENTION** : {alert['message']}")
    else:
        st.success("✅ Qualité de l'air et conditions météorologiques stables. Aucune alerte active.")

    # KPI Summary Cards
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Température", f"{latest['temperature_2m']:.1f} °C")
    col2.metric("Humidité", f"{latest['relativehumidity_2m']:.0f} %")
    col3.metric("Indice AQI (US)", f"{int(latest['us_aqi'])}")
    col4.metric("PM 2.5", f"{latest['pm2_5']:.1f} µg/m³")
    col5.metric("Score Confort (0-100)", f"{latest['health_score']:.1f}")

    today = df[df["datetime"].dt.date == latest["datetime"].date()]
    col6, col7, col8, col9, col10, col11 = st.columns(6)
    col6.metric("Ressentie", f"{latest['apparent_temperature']:.1f} °C")
    col7.metric("Min / Max du jour", f"{today['temperature_2m'].min():.0f} / {today['temperature_2m'].max():.0f} °C")
    col8.metric("Pression", f"{latest['surface_pressure']:.0f} hPa")
    col9.metric("Vent", f"{latest['windspeed_10m']:.0f} km/h ({latest['winddirection_10m']:.0f}°)")
    col10.metric("Nuages", f"{latest['cloudcover']:.0f} %")
    col11.metric("Précipitations", f"{latest['precipitation']:.1f} mm")

    # Visualizations
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Évolution Météo", "🏭 Qualité de l'Air", "🗺️ Carte Interactive", "📊 Statistiques"])

    with tab1:
        st.subheader("Évolution des métriques (historique + prévisions)")
        if selected_metrics:
            fig_temp = px.line(
                df_period, x="datetime", y=selected_metrics,
                labels={"value": "Valeur", "datetime": "Date/Heure", "variable": "Métrique"},
                title="Série temporelle"
            )
            fig_temp.add_vline(x=latest["datetime"], line_dash="dash", line_color="grey")
            st.plotly_chart(fig_temp)
            st.caption("Le trait en pointillés correspond à maintenant : à droite ce sont les prévisions.")
        else:
            st.info("Choisis au moins une métrique dans la barre latérale.")

    with tab2:
        st.subheader("Concentration des Polluants Clés (µg/m³)")
        fig_air = px.bar(
            df_past.tail(24), x="datetime", y=["pm2_5", "pm10", "nitrogen_dioxide"],
            barmode="group",
            title="Exposition aux polluants sur les 24 dernières heures"
        )
        st.plotly_chart(fig_air)

    with tab3:
        st.subheader("Indice AQI actuel des villes suivies")
        map_rows = []
        for city, coords in DEFAULT_CITIES.items():
            city_past = DataProcessor.keep_past_hours(all_data[city])
            if city_past.empty:
                continue
            aqi = city_past["us_aqi"].iloc[-1]
            map_rows.append({
                "lat": coords["lat"],
                "lon": coords["lon"],
                "city": city,
                "aqi": int(aqi),
                "categorie": DataProcessor.get_aqi_category(aqi)
            })
        map_df = pd.DataFrame(map_rows)
        fig_map = px.scatter_map(
            map_df, lat="lat", lon="lon", hover_name="city", hover_data=["aqi"],
            color="categorie", color_discrete_map=AQI_COLORS,
            center={"lat": city_info["lat"], "lon": city_info["lon"]}, zoom=4, height=450
        )
        fig_map.update_traces(marker={"size": 18})
        fig_map.update_layout(map_style="open-street-map")
        st.plotly_chart(fig_map)

    with tab4:
        st.subheader("Moyenne, médiane et tendances")
        if selected_metrics:
            st.dataframe(DataProcessor.compute_statistics(df_past, selected_metrics))
            st.caption("Tendance = valeur actuelle moins la valeur d'il y a 24h (ou 7 jours).")
        else:
            st.info("Choisis au moins une métrique dans la barre latérale.")
