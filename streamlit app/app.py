import streamlit as st
from pathlib import Path

# Sikre korrekte stier uansett hvor appen kjøres fra
APP_DIR = Path(__file__).parent

# 🌍 Global innstilling i sidebar
st.sidebar.title("Settings")

selected_area = st.sidebar.selectbox(
    "Select area",
    ["West", "East", "North"],
    key="selected_area"
)

# 📂 Sidenavigasjon
pages = {
    "Home": [
        st.Page(APP_DIR / "Pages" / "Home.py", title="Home", icon="🏠"),
    ],

    "Explore Data": [
        st.Page(APP_DIR / "Pages" / "map.py", title="Geographic Map", icon="🗺️"),
        st.Page(APP_DIR / "Pages" / "analysis.py", title="Reservoir Data", icon="💧"),
        st.Page(APP_DIR / "Pages" / "Cross_border_flows.py", title="Electricity Flows", icon="⚡"),
        st.Page(APP_DIR / "Pages" / "weather.py", title="Weather Data", icon="🌤️"),
    ],

    "Analysis": [
        st.Page(APP_DIR / "Pages" / "Time_series_analysis.py", title="Time Series Analysis", icon="📈"),
        st.Page(APP_DIR / "Pages" / "Anomaly_analysis.py", title="Anomaly Detection", icon="🚨"),
        st.Page(APP_DIR / "Pages" / "Weather_correlation.py", title="Weather Correlation", icon="🔗"),
    ],

    "Forecasting": [
        st.Page(APP_DIR / "Pages" / "Forecasting.py", title="Reservoir Filling Forecast", icon="🔮"),
    ],

}

pg = st.navigation(pages)
pg.run()