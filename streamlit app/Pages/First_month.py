
import streamlit as st
import pandas as pd
import requests



# Load reservoir data from NVE


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
    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce"
    )

    # Remove rows without a valid date
    data = data.dropna(subset=["Date"])

    return data



# Get reservoir data


try:
    reservoir_data = load_reservoir_data()

except (requests.RequestException, ValueError) as e:
    st.error(f"Could not load reservoir data: {e}")
    st.stop()



# Select area using the global selector


st.title("Reservoirs")

# Get the selected area from app.py
selected_area = st.session_state["selected_area"]

# Map the selected area to the corresponding NVE VASS area
area_mapping = {
    "East": 1,
    "West": 2,
    "North": 3
}

selected_omrnr = area_mapping[selected_area]

# Filter the reservoir data
reservoir_data["omrnr"] = pd.to_numeric(
    reservoir_data["omrnr"],
    errors="coerce"
)

reservoir_data = reservoir_data[
    (reservoir_data["omrType"] == "VASS")
    & (reservoir_data["omrnr"] == selected_omrnr)
].copy()

st.write(f"Selected area: **{selected_area}**")



# Check filtered data


if reservoir_data.empty:
    st.warning(
        f"No reservoir data available for {selected_area}."
    )
    st.stop()



# Select the first month


columns = [
    "filling_level",
    "Capacity(TWh)",
    "Filled (TWh)",
    "filling_level_previous_week",
    "change_filling_level"
]

# Find the earliest date for the selected area
first_date = reservoir_data["Date"].min()

# Select the first month
first_month = reservoir_data[
    reservoir_data["Date"] < first_date + pd.DateOffset(months=1)
]

# Prepare data for the line chart column
chart_data = pd.DataFrame({
    "Variable": columns,
    "Values": [
        first_month[column].tolist()
        for column in columns
    ]
})

# Display the data
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
