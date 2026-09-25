import streamlit as st

Pages = [
    st.Page("pages/reservoirs.py", title="Reservoirs"),
    st.Page("pages/analysis.py", title="Analysis"),
    st.Page("pages/about.py", title="About")
]

pg = st.navigation(Pages)

pg.run()    