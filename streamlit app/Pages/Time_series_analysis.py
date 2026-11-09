
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram

st.title("Time Series Analysis")

st.write(
    "Explore the weather data using STL decomposition "
    "and spectrogram analysis."
)

if "weather_daily" not in st.session_state:
    st.warning(
        "No weather data found. Go to the Meteorological Data "
        "page and download weather data first."
    )
    st.stop()

# Get the downloaded daily weather data
weather_data = st.session_state["weather_daily"].copy()

# Check that the dataset contains data
if weather_data.empty:
    st.warning("The weather dataset is empty.")
    st.stop()

# Convert date column to datetime
weather_data["date"] = pd.to_datetime(
    weather_data["date"],
    errors="coerce"
)

weather_data = weather_data.dropna(subset=["date"])


st.subheader("Data selection")

# Find available numerical weather variables
numeric_columns = weather_data.select_dtypes(
    include="number"
).columns.tolist()

if not numeric_columns:
    st.error("No numerical variables found in the weather data.")
    st.stop()

# Let the user choose which variable to analyse
default_variable = (
    "temperature_2m"
    if "temperature_2m" in numeric_columns
    else numeric_columns[0]
)

selected_variable = st.selectbox(
    "Select variable",
    numeric_columns,
    index=numeric_columns.index(default_variable)
)

# Prepare the selected time series
time_series = weather_data[
    ["date", selected_variable]
].copy()

time_series = time_series.dropna()
time_series = time_series.sort_values("date")

# Use one observation per date
time_series = (
    time_series.groupby("date")[selected_variable]
    .mean()
)

# Make sure the series has enough observations
if len(time_series) < 4:
    st.warning(
        "There are too few observations for time series analysis. "
        "Download a longer period of weather data."
    )
    st.stop()

st.write(f"Selected variable: **{selected_variable}**")
st.write(f"Number of observations: **{len(time_series)}**")

# Show the original time series
st.subheader("Original time series")

st.line_chart(time_series)


stl_tab, spectrogram_tab = st.tabs(
    ["STL analysis", "Spectrogram"]
)


# STL analysis

with stl_tab:

    st.header("STL decomposition")

    st.write(
        "STL (Seasonal-Trend decomposition using Loess) "
        "separates a time series into three components: "
        "trend, seasonality and residuals."
    )

    # Select the seasonal period
    # For daily data, a period of 7 represents weekly seasonality
    max_period = max(2, len(time_series) // 2)

    default_period = min(7, max_period)

    seasonal_period = st.slider(
        "Seasonal period",
        min_value=2,
        max_value=max_period,
        value=default_period,
        help="For daily data, 7 represents a weekly seasonal pattern."
    )

    # Perform STL decomposition
    if st.button("Run STL analysis"):

        with st.spinner("Performing STL decomposition..."):

            # Fit the STL model
            stl_model = STL(
                time_series,
                period=seasonal_period,
                robust=True
            )

            stl_result = stl_model.fit()

            # Create a figure with four subplots
            fig, axes = plt.subplots(
                4,
                1,
                figsize=(12, 9),
                sharex=True
            )

            # Original time series
            axes[0].plot(time_series.index, time_series.values)
            axes[0].set_title("Original time series")
            axes[0].set_ylabel(selected_variable)

            # Trend component
            axes[1].plot(
                time_series.index,
                stl_result.trend
            )
            axes[1].set_title("Trend")
            axes[1].set_ylabel("Trend")

            # Seasonal component
            axes[2].plot(
                time_series.index,
                stl_result.seasonal
            )
            axes[2].set_title("Seasonality")
            axes[2].set_ylabel("Seasonal")

            # Residual component
            axes[3].plot(
                time_series.index,
                stl_result.resid
            )
            axes[3].set_title("Residuals")
            axes[3].set_ylabel("Residuals")
            axes[3].set_xlabel("Date")

            # Improve the layout
            plt.tight_layout()

            # Display the figure
            st.pyplot(fig)

            plt.close(fig)

            st.success("STL analysis completed successfully!")


#Spectrogram analysis

with spectrogram_tab:

    st.header("Spectrogram analysis")

    st.write(
        "A spectrogram shows how the frequency content of a "
        "time series changes over time. It can help identify "
        "repeating patterns and periodic behaviour."
    )

    # Select the window length
    window_length = st.slider(
        "Window length",
        min_value=4,
        max_value=len(time_series),
        value=min(8, len(time_series)),
        help="Number of observations used in each spectrogram window."
    )

    # Calculate the spectrogram
    if st.button("Generate spectrogram"):

        with st.spinner("Calculating spectrogram..."):

            # Convert the time series to a numerical array
            values = time_series.values.astype(float)

            # Calculate the spectrogram
            frequencies, times, power = spectrogram(
                values,
                fs=1,  # One observation per day
                nperseg=window_length,
                noverlap=window_length // 2,
                detrend="linear",
                scaling="density"
            )

            # Remove zero frequency because its period is infinite
            nonzero_frequency = frequencies > 0

            frequencies = frequencies[nonzero_frequency]
            power = power[nonzero_frequency, :]

            # Convert frequency to decibels
            power_db = 10 * np.log10(power + 1e-12)

            # Convert relative time to dates
            spectrogram_dates = (
                time_series.index[0]
                + pd.to_timedelta(times, unit="D")
            )

            # Create the spectrogram plot
            fig, ax = plt.subplots(figsize=(12, 6))

            image = ax.pcolormesh(
                spectrogram_dates,
                frequencies,
                power_db,
                shading="auto"
            )

            # Add labels and title
            ax.set_title("Spectrogram")
            ax.set_xlabel("Date")
            ax.set_ylabel("Frequency (cycles per day)")

            # Add colorbar
            fig.colorbar(
                image,
                ax=ax,
                label="Power (dB)"
            )

            plt.tight_layout()

            # Display the figure
            st.pyplot(fig)

            plt.close(fig)

            st.success("Spectrogram generated successfully!")
