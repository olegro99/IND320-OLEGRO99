import streamlit as st
import pandas as pd

@st.cache_data
def load_reservoir_data():
    data = pd.read_csv("../data/reservoirs_processed.csv")

    data = data.rename(columns={
        "dato_Id": "Date",
        "fyllingsgrad": "filling_level",
        "kapasitet_TWh": "Capacity(TWh)",
        "fylling_TWh": "Filled (TWh)",
        "fyllingsgrad_forrige_uke": "filling_level_previous_week",
        "endring_fyllingsgrad": "change_filling_level"
    })

    data["Date"] = pd.to_datetime(data["Date"])

    return data


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

