import streamlit as st
import pandas as pd

@st.cache_data
def load_reservoir_data():
    data = pd.read_csv("../data/reservoirs.csv")
    return data

tab1, tab2 = st.tabs(["Reservoirs Data", "Reservoirs Analysis"])
reservoir_data = load_reservoir_data()
tab1.line_chart(
    reservoir_data,
    y=[
        "filling_level",
        "Filled (TWh)",
        "filling_level_previous_week",
        "change_filling_level"
    ]
)
tab2.dataframe(reservoir_data)
