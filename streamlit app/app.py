import streamlit as st

pages = [
    st.Page("Pages/Home.py", title="Home"),
    st.Page("Pages/First_month.py", title="First Month"),
    st.Page("Pages/analysis.py", title="Analysis"),
    st.Page("Pages/test.py", title="Test"),
]

pg = st.navigation(pages)

pg.run()