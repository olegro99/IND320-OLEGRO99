
import streamlit as st

st.title("Home")
st.write("Welcome to Ole's Streamlit app!")

st.subheader("About")

assignment_summaries = [
    {
        "title": "Assignment 1 – Basic Data Processing and Streamlit",
        "summary": """
        - Create a GitHub repository and deploy a Streamlit application.
        - Import and process reservoir data from a CSV file using Pandas.
        - Explore and visualize the data using tables and plots.
        - Build a multi-page Streamlit application with navigation,
          interactive tables and plots.
        - Implement caching to improve application performance.
        """
    },
    {
        "title": "Assignment 2 – APIs and Databases",
        "summary": """
        - Set up and connect Cassandra, Spark and MongoDB.
        - Retrieve reservoir data directly from the NVE API.
        - Retrieve cross-border electricity flow data from ENTSO-E.
        - Use Spark to process and filter large datasets.
        - Store processed data in MongoDB.
        - Visualize electricity flows using pie charts and line plots.
        - Extend the Streamlit application with API and MongoDB
          integration and interactive selections for areas, years
          and months.
        """
    },
    {
        "title": "Assignment 3 – Weather Data and Time Series Analysis",
        "summary": """
        - Retrieve historical weather data from Open-Meteo using ERA5.
        - Use geographical shapefiles from NVE Atlas to retrieve
          weather data for Norwegian regions.
        - Use DCT and Statistical Process Control (SPC) to detect
          precipitation outliers.
        - Use Local Outlier Factor (LOF) to detect temperature anomalies.
        - Perform STL decomposition to analyse trends, seasonal
          patterns and residuals in reservoir filling data.
        - Create spectrograms to investigate frequency components
          in time series data.
        - Extend the Streamlit application with dedicated analysis
          pages, tabs and interactive visualizations.
        """
    },
    {
        "title": "Assignment 4 – Forecasting, Interactive Maps and Improvements",
        "summary": """
        - Retrieve EUR and USD exchange rates from the Norwegian Bank's API.
        - Investigate and handle timezone differences between
          the different data sources.
        - Develop a forecasting function using River (SARIMAX or
          machine learning) to predict future reservoir filling.
        - Refactor the Streamlit application with improved structure,
          navigation and a consistent visual theme.
        - Replace static plots with dynamic and interactive
          Plotly visualizations.
        - Create interactive GeoJSON-based maps with selectable
          areas, time periods and data variables.
        - Analyse relationships between weather data and reservoir
          filling using Sliding Window Correlation.
        - Develop an interactive forecasting page with selectable
          training periods, forecast horizons and exogenous variables.
        - Implement at least one bonus feature, such as caching,
          error handling or confidence intervals.
        """
    }
]

for assignment in assignment_summaries:
    with st.expander(assignment["title"]):
        st.markdown(assignment["summary"])

st.divider()

st.subheader("Overall Project Goal")

st.write("""
The goal of the project is to develop a comprehensive analysis
platform combining data from multiple APIs and databases, including
reservoir data, electricity flows, weather data and currency
exchange rates.

The platform uses statistical analysis, anomaly detection and
machine learning-based forecasting to explore and predict
reservoir filling levels.
""")
