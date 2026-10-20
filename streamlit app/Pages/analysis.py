
import streamlit as st
import pandas as pd
import requests
import plotly.express as px


@st.cache_data(ttl=3600)
def load_reservoir_data():
    # Fetch reservoir data from the NVE API
    url = (
        "https://biapi.nve.no/magasinstatistikk/"
        "api/Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = pd.DataFrame(response.json())

    # Rename columns to English
    data = data.rename(columns={
        "dato_Id": "Date",
        "omrType": "area_type",
        "omrnr": "area_number",
        "fyllingsgrad": "filling_level",
        "kapasitet_TWh": "Capacity(TWh)",
        "fylling_TWh": "Filled (TWh)",
        "fyllingsgrad_forrige_uke": "filling_level_previous_week",
        "endring_fyllingsgrad": "change_filling_level"
    })

    # Convert dates to datetime
    data["Date"] = pd.to_datetime(
        data["Date"], errors="coerce"
    )

    # Remove rows without a valid date
    data = data.dropna(subset=["Date"])

    # Clean area information
    data["area_type"] = (
        data["area_type"].astype("string").str.upper()
    )
    data["area_number"] = data["area_number"].astype("string")

    # Convert measurement columns to numeric values
    columns = [
        "filling_level",
        "Capacity(TWh)",
        "Filled (TWh)",
        "filling_level_previous_week",
        "change_filling_level"
    ]

    for column in columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    return data


# Load data from the API
try:
    reservoir_data = load_reservoir_data()
except (requests.RequestException, ValueError, KeyError) as e:
    st.error(f"Could not load reservoir data: {e}")
    st.stop()


st.title("Reservoir data analysis")

# Choose the type of area
available_types = [
    area for area in ["EL", "NO", "VASS"]
    if area in reservoir_data["area_type"].dropna().unique()
]

if not available_types:
    st.error("No EL, NO or VASS areas were found in the data.")
    st.stop()

area_type = st.radio(
    "Select area type",
    options=available_types,
    horizontal=True
)

# Filter data according to the selected area type
area_data = reservoir_data[
    reservoir_data["area_type"] == area_type
].copy()

# Columns that can be plotted
columns = [
    "filling_level",
    "Capacity(TWh)",
    "Filled (TWh)",
    "filling_level_previous_week",
    "change_filling_level"
]

# Select measurement
selected_column = st.selectbox(
    "Select data to display",
    ["All"] + columns
)

# Find the available months for the selected area type
months = sorted(
    area_data["Date"].dt.to_period("M").unique()
)

if len(months) == 0:
    st.warning("No data is available for this area type.")
    st.stop()

# Select one month
selected_month = st.select_slider(
    "Select month",
    options=months,
    value=months[-1],
    format_func=lambda month: str(month)
)

# Filter data for the selected month
filtered_data = area_data[
    area_data["Date"].dt.to_period("M") == selected_month
].copy()

# Sort observations chronologically
filtered_data = filtered_data.sort_values("Date")

if filtered_data.empty:
    st.warning("No data is available for the selected month.")
    st.stop()

# Create plots with one line per area number
if selected_column == "All":

    for column in columns:
        plot_data = filtered_data.dropna(
            subset=["Date", "area_number", column]
        )

        if plot_data.empty:
            continue

        fig = px.line(
            plot_data,
            x="Date",
            y=column,
            color="area_number",
            title=f"{column} by area number",
            labels={
                "Date": "Date",
                column: column,
                "area_number": "Area number"
            }
        )

        fig.update_layout(
            hovermode="x unified",
            legend_title_text="Area number"
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    plot_data = filtered_data.dropna(
        subset=["Date", "area_number", selected_column]
    )

    if plot_data.empty:
        st.warning("No values are available for this measurement.")
    else:
        fig = px.line(
            plot_data,
            x="Date",
            y=selected_column,
            color="area_number",
            title=f"{selected_column} by area number",
            labels={
                "Date": "Date",
                selected_column: selected_column,
                "area_number": "Area number"
            }
        )

        fig.update_layout(
            hovermode="x unified",
            legend_title_text="Area number"
        )

        st.plotly_chart(fig, use_container_width=True)
