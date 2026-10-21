<<<<<<< HEAD
import streamlit as st
import pandas as pd

@st.cache_data
def load_reservoir_data():
    data = pd.read_csv("D2Dbook/data/reservoirs_processed.csv")

=======

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
>>>>>>> Assignment-2-branch
    data = data.rename(columns={
        "dato_Id": "Date",
        "fyllingsgrad": "filling_level",
        "kapasitet_TWh": "Capacity(TWh)",
        "fylling_TWh": "Filled (TWh)",
        "fyllingsgrad_forrige_uke": "filling_level_previous_week",
        "endring_fyllingsgrad": "change_filling_level"
    })

<<<<<<< HEAD
    data["Date"] = pd.to_datetime(data["Date"])
=======
    # Convert dates to datetime
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    # Remove rows without a valid date
    data = data.dropna(subset=["Date"])
>>>>>>> Assignment-2-branch

    return data


<<<<<<< HEAD
reservoir_data = load_reservoir_data()

st.title("Reservoirs")

# First month
first_month = reservoir_data[
    reservoir_data["Date"] < reservoir_data["Date"].min() + pd.DateOffset(months=1)
]

chart_data = pd.DataFrame({
    "Variable": [
        "filling_level",
        "Capacity(TWh)",
        "Filled (TWh)",
        "filling_level_previous_week",
        "change_filling_level"
    ],
    "Values": [
        first_month["filling_level"].tolist(),
        first_month["Capacity(TWh)"].tolist(),
        first_month["Filled (TWh)"].tolist(),
        first_month["filling_level_previous_week"].tolist(),
        first_month["change_filling_level"].tolist()
=======
try:
    reservoir_data = load_reservoir_data()
except (requests.RequestException, ValueError) as e:
    st.error(f"Could not load reservoir data: {e}")
    st.stop()


st.title("Reservoirs")

# Define the columns to display
columns = [
    "filling_level",
    "Capacity(TWh)",
    "Filled (TWh)",
    "filling_level_previous_week",
    "change_filling_level"
]

if reservoir_data.empty:
    st.warning("No reservoir data is available.")
    st.stop()

# Select the first month based on the earliest date
first_date = reservoir_data["Date"].min()
first_month = reservoir_data[
    reservoir_data["Date"] < first_date + pd.DateOffset(months=1)
]

# Prepare data for the line chart column
chart_data = pd.DataFrame({
    "Variable": columns,
    "Values": [
        first_month[column].tolist()
        for column in columns
>>>>>>> Assignment-2-branch
    ]
})

st.dataframe(
    chart_data,
    column_config={
        "Values": st.column_config.LineChartColumn(
            "First month",
            width="large"
        )
    },
    hide_index=True
)
<<<<<<< HEAD

=======
>>>>>>> Assignment-2-branch
