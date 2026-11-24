import streamlit as st

# Global settings
st.sidebar.title("Settings")

selected_area = st.sidebar.selectbox(
    "Select area",
    ["West", "East", "North"],
    key="selected_area"
)

# Page navigation
pages = {
    "Overview": [
        st.Page("Pages/Home.py", title="Home"),
        st.Page("Pages/First_month.py", title="First Month"),
    ],

    "Norway": [
        st.Page("Pages/weather.py", title="Meteorological Data"),
        st.Page("Pages/Time_series_analysis.py", title="Time Series Analysis"),
        st.Page("Pages/Anomaly_analysis.py", title="Anomaly Analysis"),
        st.Page("Pages/analysis.py", title="Reservoir Analysis"),
        st.Page("Pages/map.py", title="Map"),
        st.Page("Pages/test map.py", title = "test") 
    ],

    "Cross-border": [
        st.Page("Pages/Cross_border_flows.py", title="Cross-border Flows"),
    ],
}

pg = st.navigation(pages)
pg.run()