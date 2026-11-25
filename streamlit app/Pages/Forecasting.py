import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

from functions.machine_learning import (
    forecast_reservoir_filling,
    get_nve_monthly_data,
)

st.title("Reservoir filling forecast")

# Download and prepare monthly NVE data
nve_monthly = get_nve_monthly_data(area_number=1)

# Select historical period
start_date = st.date_input(
    "Start date",
    value=nve_monthly.index.min().date(),
)

end_date = st.date_input(
    "End date",
    value=nve_monthly.index.max().date(),
)

# Filter data based on selected period
selected_data = nve_monthly.loc[
    (nve_monthly.index >= pd.Timestamp(start_date))
    & (nve_monthly.index <= pd.Timestamp(end_date))
].copy()

# Select forecast horizon
horizon = st.slider(
    "Forecast horizon (months)",
    min_value=1,
    max_value=6,
    value=3,
)

# Generate forecast
forecast, model, train_data = forecast_reservoir_filling(
    monthly_data=selected_data,
    history_months=12,
    horizon_months=horizon,
)

fig = go.Figure()

# Historical data (blue)
fig.add_trace(go.Scatter(
    x=train_data.index,
    y=train_data["fyllingsgrad"],
    mode="lines",
    name="Historical",
    line=dict(color="blue")
))

# Forecast (red)
fig.add_trace(go.Scatter(
    x=forecast.index,
    y=forecast,
    mode="lines+markers",
    name="Forecast",
    line=dict(color="red", dash="dash")
))

fig.update_layout(
    title="Reservoir filling forecast",
    xaxis_title="Date",
    yaxis_title="Filling degree",
    legend_title="Data",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)