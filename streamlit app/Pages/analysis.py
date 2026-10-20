
import streamlit as st
import pandas as pd
import requests


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
        "fyllingsgrad": "filling_level",
        "kapasitet_TWh": "Capacity(TWh)",
        "fylling_TWh": "Filled (TWh)",
        "fyllingsgrad_forrige_uke": "filling_level_previous_week",
        "endring_fyllingsgrad": "change_filling_level"
    })

    # Convert dates to datetime
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    # Remove rows without a valid date
    data = data.dropna(subset=["Date"])

    return data


try:
    reservoir_data = load_reservoir_data()
except (requests.RequestException, ValueError) as e:
    st.error(f"Could not load reservoir data: {e}")
    st.stop()


st.title("Reservoir data analysis")

# Columns that can be plotted
columns = [
    "filling_level",
    "Capacity(TWh)",
    "Filled (TWh)",
    "filling_level_previous_week",
    "change_filling_level"
]

# Select one column or all columns
selected_column = st.selectbox(
    "Select data to display",
    ["All"] + columns
)

# Create a list of available months
months = sorted(
    reservoir_data["Date"].dt.to_period("M").unique()
)

if not months:
    st.warning("No reservoir data is available.")
    st.stop()

# Select month
selected_month = st.select_slider(
    "Select month",
    options=months,
    value=months[0],
    format_func=lambda month: str(month)
)

# Filter data based on selected month
filtered_data = reservoir_data[
    reservoir_data["Date"].dt.to_period("M") == selected_month
]

# Plot the selected data
if selected_column == "All":
    st.line_chart(
        filtered_data.set_index("Date")[columns],
        y_label="Value",
        x_label="Date"
    )
else:
    st.line_chart(
        filtered_data.set_index("Date"),
        y=selected_column,
        y_label=selected_column,
        x_label="Date"
    )
