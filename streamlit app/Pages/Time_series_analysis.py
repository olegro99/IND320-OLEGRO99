

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram


# Apply the dashboard color theme to Plotly figures
def apply_plot_theme(fig):

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#EAF6FF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="sans serif",
            color="#16324F"
        ),
        colorway=[
            "#168AAD",
            "#52B6CF",
            "#1D4E89",
            "#90D5EC"
        ],
        margin=dict(l=40, r=30, t=60, b=40),
        hovermode="x unified"
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#D6ECFA"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#D6ECFA"
    )

    return fig


st.title("Time Series Analysis")

st.write(
    "Explore the weather data using STL decomposition "
    "and spectrogram analysis."
)


# Check if weather data is available
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

# Define available weather properties
weather_variables = {
    "Temperature": "temperature_2m",
    "Precipitation": "precipitation",
    "Relative humidity": "relative_humidity_2m",
    "Wind speed": "wind_speed_10m"
}

# Keep only variables that exist in the dataset
available_variables = {
    name: column
    for name, column in weather_variables.items()
    if column in numeric_columns
}

if not available_variables:
    st.error("No supported weather variables found.")
    st.stop()

# Select weather property, with Temperature as default
variable_names = list(available_variables.keys())

default_index = (
    variable_names.index("Temperature")
    if "Temperature" in variable_names
    else 0
)

selected_property = st.selectbox(
    "Select weather property",
    variable_names,
    index=default_index
)

selected_variable = available_variables[selected_property]


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


st.write(f"Selected weather property: **{selected_property}**")
st.write(f"Number of observations: **{len(time_series)}**")


# Display the original time series using Plotly
st.subheader("Original time series")

fig = px.line(
    x=time_series.index,
    y=time_series.values,
    labels={
        "x": "Date",
        "y": selected_variable
    },
    title="Original time series"
)

fig.update_traces(
    line=dict(color="#168AAD", width=2),
    hovertemplate=(
        "Date: %{x|%Y-%m-%d}<br>"
        + selected_variable
        + ": %{y:.2f}<extra></extra>"
    )
)

fig = apply_plot_theme(fig)

fig.update_layout(height=450)

st.plotly_chart(fig, use_container_width=True)


# Create analysis tabs
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

    # Select weather property
    weather_options = {
        "Temperature": "temperature_2m",
        "Precipitation": "precipitation",
        "Relative humidity": "relative_humidity_2m",
        "Wind speed": "wind_speed_10m"
        }

    selected_variable = st.selectbox(
        "Select weather property",
        list(weather_options.keys()),
        index=0,
        key="satv_weather_property"
        )

    # Select the corresponding weather time series
    time_series = weather_data[weather_options[selected_variable]]

    # Select the seasonal period
    max_period = max(2, len(time_series) // 2)
    default_period = min(7, max_period)

    seasonal_period = st.slider(
        "Seasonal period",
        min_value=2,
        max_value=max_period,
        value=default_period,
        help="For daily data, 7 represents a weekly seasonal pattern."
    )


    # Select seasonal smoother
    seasonal_smoother = st.slider(
        "Seasonal smoother",
        min_value=7,
        max_value=51,
        value=13,
        step=2,
        help="Controls the smoothness of the seasonal component."
    )


    # Select trend smoother
    # STL requires an odd trend window larger than the seasonal period
    min_trend = seasonal_period + 1

    if min_trend % 2 == 0:
        min_trend += 1

    default_trend = max(21, min_trend)

    if default_trend % 2 == 0:
        default_trend += 1

    max_trend = max(101, default_trend)

    trend_smoother = st.slider(
        "Trend smoother",
        min_value=min_trend,
        max_value=max_trend,
        value=default_trend,
        step=2,
        help="Controls the smoothness of the trend component."
    )


    # Select robust option
    robust = st.checkbox(
        "Robust decomposition",
        value=True,
        help="Reduces the influence of outliers."
    )


    # Perform STL decomposition
    if st.button("Run STL analysis"):

        with st.spinner("Performing STL decomposition..."):

            # Fit the STL model
            stl_model = STL(
                time_series,
                period=seasonal_period,
                seasonal=seasonal_smoother,
                trend=trend_smoother,
                robust=robust
            )

            stl_result = stl_model.fit()


            # Create four interactive subplots
            fig = make_subplots(
                rows=4,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.07,
                subplot_titles=(
                    "Original time series",
                    "Trend",
                    "Seasonality",
                    "Residuals"
                )
            )


            # Original time series
            fig.add_trace(
                go.Scatter(
                    x=time_series.index,
                    y=time_series.values,
                    mode="lines",
                    name="Original",
                    line=dict(color="#168AAD", width=2)
                ),
                row=1,
                col=1
            )


            # Trend component
            fig.add_trace(
                go.Scatter(
                    x=time_series.index,
                    y=stl_result.trend,
                    mode="lines",
                    name="Trend",
                    line=dict(color="#1D4E89", width=2)
                ),
                row=2,
                col=1
            )


            # Seasonal component
            fig.add_trace(
                go.Scatter(
                    x=time_series.index,
                    y=stl_result.seasonal,
                    mode="lines",
                    name="Seasonality",
                    line=dict(color="#52B6CF", width=2)
                ),
                row=3,
                col=1
            )


            # Residual component
            fig.add_trace(
                go.Scatter(
                    x=time_series.index,
                    y=stl_result.resid,
                    mode="lines",
                    name="Residuals",
                    line=dict(color="#F4A261", width=2)
                ),
                row=4,
                col=1
            )


            # Update subplot axes
            fig.update_yaxes(
                title_text=selected_variable,
                row=1,
                col=1
            )

            fig.update_yaxes(
                title_text="Trend",
                row=2,
                col=1
            )

            fig.update_yaxes(
                title_text="Seasonal",
                row=3,
                col=1
            )

            fig.update_yaxes(
                title_text="Residuals",
                row=4,
                col=1
            )

            fig.update_xaxes(
                title_text="Date",
                row=4,
                col=1
            )


            # Apply the dashboard theme
            fig = apply_plot_theme(fig)

            fig.update_layout(
                height=850,
                title_text="STL decomposition",
                showlegend=False
            )


            # Display the interactive figure
            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.success("STL analysis completed successfully!")


# Spectrogram analysis

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
                fs=1,
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


            # Create an interactive spectrogram using Plotly
            fig = go.Figure(
                data=go.Heatmap(
                    x=spectrogram_dates,
                    y=frequencies,
                    z=power_db,
                    colorscale="Blues",
                    colorbar=dict(
                        title="Power (dB)"
                    ),
                    hovertemplate=(
                        "Date: %{x|%Y-%m-%d}<br>"
                        "Frequency: %{y:.4f} cycles/day<br>"
                        "Power: %{z:.2f} dB"
                        "<extra></extra>"
                    )
                )
            )


            # Update layout
            fig.update_layout(
                title="Spectrogram",
                xaxis_title="Date",
                yaxis_title="Frequency (cycles per day)",
                height=600
            )


            # Apply the dashboard theme
            fig = apply_plot_theme(fig)


            # Display the interactive figure
            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.success("Spectrogram generated successfully!")
