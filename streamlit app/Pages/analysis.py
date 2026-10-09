import streamlit as st
import pandas as pd


@st.cache_data
def load_reservoir_data():
    data = pd.read_csv("D2Dbook/data/reservoirs_processed.csv")

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

# Create list of months
months = sorted(reservoir_data["Date"].dt.to_period("M").unique())

# Select months
selected_month = st.select_slider(
    "Select month",
    options=months,
    value=months[0]
)

# Filter data based on selected month
filtered_data = reservoir_data[
    reservoir_data["Date"].dt.to_period("M") == selected_month
]

# Plot
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

