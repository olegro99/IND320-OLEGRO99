
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from functions.water_functions import (
    process_water_data,
    get_water_data
)

from functions.weather_functions import (
    aggregate_weather_daily,
    download_weather
)



# Download weather data from Open-Meteo
@st.cache_data(ttl=86400, show_spinner=False)
def load_weather_from_api():

    regions = ["West", "East", "North"]
    weather_frames = []

    for region in regions:

        weather_region = download_weather(
            region=region,
            start_date="2024-01-01",
            end_date="2025-12-31",
            batch_size=10
        )

        if weather_region is None or weather_region.empty:
            raise ValueError(
                f"No weather data returned for {region}."
            )

        weather_frames.append(weather_region)

    return pd.concat(
        weather_frames,
        ignore_index=True
    )


st.title("Sliding Window Correlation")

st.write(
    "Explore how meteorological variables relate to "
    "national reservoir filling over time."
)

if st.button("Download weather data"):

    try:
        with st.spinner("Downloading weather data from Open-Meteo..."):
            weather_data = load_weather_from_api()

        st.session_state["weather_data"] = weather_data
        st.success("Weather data downloaded successfully!")

    except Exception as e:
        st.error("Unable to retrieve weather data from Open-Meteo.")
        st.warning("Please try again later.")
        st.caption(str(e))


# Only continue when weather data has been downloaded
if "weather_data" not in st.session_state:
    st.info("Click 'Download weather data' to load the data and display the correlation plot.")
    st.stop()

weather_data = st.session_state["weather_data"]



def aggregate_weather_weekly(weather_data):

    data = weather_data.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        utc=True
    )

    # Aggregate hourly data to daily values
    daily = aggregate_weather_daily(data)

    # Average across all weather regions
    daily_national = daily.groupby("date").agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        relative_humidity_2m=("relative_humidity_2m", "mean"),
        wind_speed_10m=("wind_speed_10m", "mean")
    )

    # Aggregate daily values to weekly values
    weekly = daily_national.resample("W-SUN").agg({
        "temperature_2m": "mean",
        "precipitation": "sum",
        "relative_humidity_2m": "mean",
        "wind_speed_10m": "mean"
    })

    # Only keep complete weeks
    weekly["days"] = daily_national.resample("W-SUN").size()
    weekly = weekly[weekly["days"] == 7]

    return weekly.drop(columns="days").reset_index()


weather_weekly = aggregate_weather_weekly(weather_data)


# Select national reservoir data
water_no = water_df[
    water_df["omrType"] == "NO"
].copy()

water_no = water_no.rename(
    columns={"dato_Id": "date"}
)

water_no = water_no[["date", "fyllingsgrad"]].copy()

water_no["date"] = pd.to_datetime(
    water_no["date"],
    utc=True
)


# Merge weather and reservoir data
combined_data = pd.merge(
    weather_weekly,
    water_no,
    on="date",
    how="inner"
).sort_values("date").reset_index(drop=True)


if combined_data.empty:
    st.warning("No matching weather and reservoir data found.")
    st.stop()


missing_values = combined_data.isna().sum()

if missing_values.any():
    st.warning("Missing values detected in the dataset.")

    st.dataframe(
        missing_values[missing_values > 0]
    )


def calculate_rolling_correlation(
    data,
    weather_variable,
    lag,
    window_length
):

    result = data.copy()

    # Shift weather variable to compare earlier weather
    # with later reservoir filling
    result["weather_lagged"] = result[weather_variable].shift(lag)

    # Calculate rolling correlation
    result["correlation"] = (
        result["weather_lagged"]
        .rolling(window=window_length)
        .corr(result["fyllingsgrad"])
    )

    return result


st.title("Sliding Window Correlation")

st.write(
    "Explore how meteorological variables relate to "
    "national reservoir filling over time."
)


# Select weather variable
weather_variable = st.selectbox(
    "Select meteorological variable",
    options=[
        "temperature_2m",
        "precipitation",
        "relative_humidity_2m",
        "wind_speed_10m"
    ],
    format_func=lambda x: {
        "temperature_2m": "Temperature",
        "precipitation": "Precipitation",
        "relative_humidity_2m": "Relative humidity",
        "wind_speed_10m": "Wind speed"
    }[x]
)


# Select lag
lag = st.slider(
    "Lag (weeks)",
    min_value=0,
    max_value=20,
    value=4
)


# Select window length
window_length = st.slider(
    "Window length (weeks)",
    min_value=8,
    max_value=52,
    value=12
)


# Calculate correlation
correlation_data = calculate_rolling_correlation(
    data=combined_data,
    weather_variable=weather_variable,
    lag=lag,
    window_length=window_length
)


# Plot correlation
fig = px.line(
    correlation_data,
    x="date",
    y="correlation",
    title=f"Rolling correlation: {weather_variable}",
    labels={
        "date": "Date",
        "correlation": "Pearson correlation"
    }
)

fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray"
)

fig.update_yaxes(range=[-1, 1])

st.plotly_chart(fig, use_container_width=True)
