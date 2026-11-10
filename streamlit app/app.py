
import streamlit as st

# Global settings
st.sidebar.title("Settings")

selected_area = st.sidebar.selectbox(
    "Select area",
    ["West", "East", "North"],
    key="selected_area"
)

# Pages
pages = [
    
    st.Page("Pages/Home.py", title="Home"),
    st.Page("Pages/First_month.py", title="First Month"),
    st.Page("Pages/weather.py", title="Meteorological Data"),
    st.Page("Pages/Time_series_analysis.py", title="Time Series Analysis"),
    st.Page("Pages/Anomaly_analysis.py", title="Anomaly Analysis"),
    st.Page("Pages/analysis.py", title="Analysis"),
    st.Page("Pages/test.py", title="Test"),
    st.Page(
        "Pages/Cross_border_flows.py",
        title="Cross-border flows"
    ),
    
]

pg = st.navigation(pages)
pg.run()