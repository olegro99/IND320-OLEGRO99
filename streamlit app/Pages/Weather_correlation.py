import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import plotly.express as px

# Define the project root directory and add it to the Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import functions for processing and retrieving reservoir data
from functions.water_functions import (
    process_water_data,
    get_water_data
)

# Import functions for retrieving and aggregating weather data
from functions.weather_functions import (
    aggregate_weather_daily,
    download_weather
)


# Download weather data from Open-Meteo
# Cache the result for 24 hours to avoid unnecessary API requests
@st.cache_data(ttl=86400, show_spinner=False)
def load_weather_from_api():

    regions = ["West", "East", "North"]
    weather_frames = []

    # Download weather data for each region
    for region in regions:

        weather_region = download_weather(
            region=region,
            start_date="2024-01-01",
            end_date="2025-12-31",
            batch_size=10
        )

        # Check whether the API returned valid data
        if weather_region is None or weather_region.empty:
            raise ValueError(
                f"No weather data returned for {region}."
            )

        weather_frames.append(weather_region)

    # Combine weather data from all regions into one DataFrame
    return pd.concat(
        weather_frames,
        ignore_index=True
    )


# Display the page title and introduction
st.title("Sliding Window Correlation")

st.write(
    "Explore how meteorological variables relate to "
    "national reservoir filling over time."
)


# Download weather data when the button is clicked
if st.button("Download weather data"):

    try:
        # Display a loading indicator while retrieving weather data
        with st.spinner("Downloading weather data from Open-Meteo..."):
            weather_data = load_weather_from_api()

        # Store the downloaded data in the session state
        st.session_state["weather_data"] = weather_data
        st.success("Weather data downloaded successfully!")

    except Exception as e:
        # Handle errors during the API request
        st.error("Unable to retrieve weather data from Open-Meteo.")
        st.warning("Please try again later.")
        st.caption(str(e))


# Only continue when weather data has been downloaded
if "weather_data" not in st.session_state:
    st.info("Click 'Download weather data' to load the data and display the correlation plot.")
    st.stop()

# Retrieve the weather data from the session state
weather_data = st.session_state["weather_data"]


# Aggregate hourly weather data into weekly observations
def aggregate_weather_weekly(weather_data):

    data = weather_data.copy()

    # Convert dates to UTC datetime format
    data["date"] = pd.to_datetime(
        data["date"],
        utc=True
    )

    # Aggregate hourly observations into daily values
    daily = aggregate_weather_daily(data)

    # Calculate national daily averages across all weather regions
    daily_national = daily.groupby("date").agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        relative_humidity_2m=("relative_humidity_2m", "mean"),
        wind_speed_10m=("wind_speed_10m", "mean")
    )

    # Aggregate daily observations into weekly values
    weekly = daily_national.resample("W-SUN").agg({
        "temperature_2m": "mean",
        "precipitation": "sum",
        "relative_humidity_2m": "mean",
        "wind_speed_10m": "mean"
    })

    # Count the number of daily observations in each week
    weekly["days"] = daily_national.resample("W-SUN").size()

    # Keep only weeks containing all seven daily observations
    weekly = weekly[weekly["days"] == 7]

    return weekly.drop(columns="days").reset_index()


# Generate weekly national weather data
weather_weekly = aggregate_weather_weekly(weather_data)


# Select national reservoir data
water_no = water_df[
    water_df["omrType"] == "NO"
].copy()

# Rename the date column to match the weather dataset
water_no = water_no.rename(
    columns={"dato_Id": "date"}
)

# Keep only the date and reservoir filling columns
water_no = water_no[["date", "fyllingsgrad"]].copy()

# Convert dates to UTC datetime format
water_no["date"] = pd.to_datetime(
    water_no["date"],
    utc=True
)


# Merge weekly weather data with national reservoir filling data
combined_data = pd.merge(
    weather_weekly,
    water_no,
    on="date",
    how="inner"
).sort_values("date").reset_index(drop=True)


# Check whether the merge returned any matching observations
if combined_data.empty:
    st.warning("No matching weather and reservoir data found.")
    st.stop()


# Check for missing values in the combined dataset
missing_values = combined_data.isna().sum()

if missing_values.any():
    st.warning("Missing values detected in the dataset.")

    st.dataframe(
        missing_values[missing_values > 0]
    )


# Calculate rolling correlation between weather variables
# and national reservoir filling
def calculate_rolling_correlation(
    data,
    weather_variable,
    lag,
    window_length
):

    result = data.copy()

    # Shift the weather variable to compare earlier weather
    # conditions with later reservoir filling
    result["weather_lagged"] = result[weather_variable].shift(lag)

    # Calculate Pearson correlation over a rolling time window
    result["correlation"] = (
        result["weather_lagged"]
        .rolling(window=window_length)
        .corr(result["fyllingsgrad"])
    )

    return result


# Display the page title and description
st.title("Sliding Window Correlation")

st.write(
    "Explore how meteorological variables relate to "
    "national reservoir filling over time."
)


# Allow the user to select a meteorological variable
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


# Allow the user to select the time lag in weeks
lag = st.slider(
    "Lag (weeks)",
    min_value=0,
    max_value=20,
    value=4
)


# Allow the user to select the rolling window length in weeks
window_length = st.slider(
    "Window length (weeks)",
    min_value=8,
    max_value=52,
    value=12
)


# Calculate the rolling correlation using the selected settings
correlation_data = calculate_rolling_correlation(
    data=combined_data,
    weather_variable=weather_variable,
    lag=lag,
    window_length=window_length
)


# Create an interactive line plot of the rolling correlation
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

# Add a horizontal reference line at zero correlation
fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray"
)

# Set the y-axis range to the possible Pearson correlation values
fig.update_yaxes(range=[-1, 1])

# Display the interactive plot in Streamlit
st.plotly_chart(fig, use_container_width=True)