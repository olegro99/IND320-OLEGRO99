import pandas as pd
import streamlit as st

# Load the dataset
@st.cache_data
def load_reservoir() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")
    data = pd.read_csv(DATA_FILE, parse_dates=["dato_Id"])
    data["fyllingsgrad_pct"] = data["fyllingsgrad"] * 100
    data["endring_pct"] = data["endring_fyllingsgrad"] * 100
    return data

