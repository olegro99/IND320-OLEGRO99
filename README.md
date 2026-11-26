# IND320 – Energy Data Analysis and Visualization

## Project Overview

This project was developed as part of the IND320 course. The objective is to collect, process, store, analyse and visualize energy-related data using different data technologies, APIs and database solutions.

The project focuses on Norwegian reservoir statistics, meteorological data and cross-border electricity flows. Data is collected from external APIs, processed using Python and stored or retrieved through database solutions. The results are presented through an interactive Streamlit web application.

## Features

### Reservoir Statistics
- Retrieve Norwegian reservoir data from the NVE Magasinstatistikk API.
- Process and visualize reservoir filling levels.
- Explore reservoir statistics across different areas.

### Weather Data and Analysis
- Retrieve historical weather data from the Open-Meteo API.
- Analyse meteorological variables such as temperature, precipitation, relative humidity and wind speed.
- Explore correlations between weather variables and national reservoir filling using sliding window correlation.
- Visualize weather information on an interactive map.

### Interactive Map
- Display Norwegian geographical regions and bidding areas.
- Visualize reservoir filling levels and meteorological variables.
- Explore different geographical areas through interactive map layers and tooltips.

### Forecasting and Time Series Analysis
- Use SARIMAX models for forecasting.
- Explore time series patterns and trends.
- Analyse seasonal components and other time series characteristics.

### Anomaly Analysis
- Identify unusual observations in energy and weather-related datasets.
- Explore different anomaly detection methods.

### Cross-border Electricity Flows
- Collect electricity flow data between Norway and neighbouring countries using the ENTSO-E API.
- Process and store electricity flow data.
- Explore cross-border electricity exchanges through interactive visualizations.

### Data Processing and Storage
- Process and transform datasets using Python, Pandas and PySpark.
- Store and retrieve data using MongoDB Atlas.
- Use Jupyter Notebooks for data exploration, model development and evaluation.

### Error Handling
- Handle API connection failures and missing data.
- Detect empty datasets and missing values.
- Display informative error and warning messages in the Streamlit application.

## Project Structure

```text
IND320-OLEGRO99/
│
├── Notebooks/                       # Jupyter notebooks and data analysis
│
├──images                            # skecth
│
├── streamlit app/
│   │
│   ├── app.py                       # Main Streamlit application
│   │
│   ├── data/                        # Geographical data and supporting files
│   │   ├── Budområder/
│   │   ├── geojson/
│   │   └── NVE region/
│   │
│   ├── functions/                   # Reusable functions
│   │   ├── __init__.py
│   │   ├── convert_geojson.py
│   │   ├── download_entsoe_prices.py
│   │   ├── machine_learning.py
│   │   ├── Mangodb.py
│   │   ├── water_functions.py
│   │   └── weather_functions.py
│   │
│   └── Pages/                       # Streamlit application pages
│       ├── analysis.py
│       ├── Anomaly_analysis.py
│       ├── check.py
│       ├── Cross_border_flows.py
│       ├── First_month.py
│       ├── Forecasting.py
│       ├── Home.py
│       ├── map.py
│       ├── Time_series_analysis.py
│       ├── Weather_correlation.py
│       └── weather.py
│                           
├── .gitignore                       # Files excluded from Git
├── README.md                        # Project documentation
└── requirements.txt                 # Python dependencies
```
