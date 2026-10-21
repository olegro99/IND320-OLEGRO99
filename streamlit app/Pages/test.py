<<<<<<< HEAD
import pandas as pd
import streamlit as st
=======

import streamlit as st
from Mangodb import get_data

st.title("MongoDB test")

try:
    df = get_data()

    st.success("Data hentet fra MongoDB!")
    st.write(f"Antall rader: {len(df)}")
    st.dataframe(df.head())

except Exception as e:
    st.error(f"Kunne ikke hente data fra MongoDB: {e}")

>>>>>>> Assignment-2-branch
