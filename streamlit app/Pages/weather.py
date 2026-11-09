
import streamlit as st
import pandas as pd
from datetime import date

from weather_functions import (
    download_weather,
    aggregate_weather_daily
)


st.title("Meteorological Data")

# Retrieve the selected area from the global selector in app.py
selected_area = st.session_state["selected_area"]

st.write(f"Selected area: **{selected_area}**")



# Create two columns for the date selectors
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start date",
        value=date(2026, 10, 12),
        key="weather_start_date"
    )

with col2:
    end_date = st.date_input(
        "End date",
        value=date(2026, 10, 26),
        key="weather_end_date"
    )



# Cache weather data for one hour.
# Different areas and date ranges are cached separately.
@st.cache_data(ttl=3600)
def get_weather_data(region, start, end):

    # Download hourly weather data from Open-Meteo
    hourly_data = download_weather(
        region=region,
        start_date=start,
        end_date=end
    )

    # Aggregate hourly observations into daily values
    daily_data = aggregate_weather_daily(hourly_data)

    return hourly_data, daily_data


# Download data when the button is clicked
if st.button("Download weather data"):

    if start_date > end_date:

        st.error("Start date must be before end date.")

    else:

        try:
            with st.spinner(
                f"Downloading weather data for {selected_area}..."
            ):

                # Download data for the currently selected area
                hourly_data, daily_data = get_weather_data(
                    selected_area,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )

                # Save downloaded data in session state
                st.session_state["weather_hourly"] = hourly_data
                st.session_state["weather_daily"] = daily_data

                # Save the area and date range associated with the data
                st.session_state["weather_area"] = selected_area
                st.session_state["weather_dates"] = (
                    start_date,
                    end_date
                )

            st.success(
                f"Weather data for {selected_area} downloaded successfully!"
            )

        except Exception as e:

            st.error(f"Could not download weather data: {e}")




# Check whether weather data has already been downloaded
if "weather_daily" in st.session_state:

    downloaded_area = st.session_state["weather_area"]

    downloaded_dates = st.session_state["weather_dates"]

    # Check if downloaded data matches the selected area and dates
    if downloaded_area != selected_area:

        st.info(
            f"The currently displayed data belongs to {downloaded_area}. "
            f"Click 'Download weather data' to download data for "
            f"{selected_area}."
        )

    elif downloaded_dates != (start_date, end_date):

        st.info(
            "The selected date range differs from the downloaded data. "
            "Click 'Download weather data' to update it."
        )

    else:

        daily_data = st.session_state["weather_daily"]

        if not daily_data.empty:

            # Display downloaded weather data
            st.subheader(
                f"Daily weather data - {selected_area}"
            )

            st.dataframe(
                daily_data,
                use_container_width=True
            )

    

            # Display daily average temperature
            st.subheader("Temperature")

            st.line_chart(
                daily_data.set_index("date")["temperature_2m"],
                y_label="Temperature (°C)"
            )

      

            # Display daily total precipitation
            st.subheader("Precipitation")

            st.bar_chart(
                daily_data.set_index("date")["precipitation"],
                y_label="Precipitation (mm)"
            )

            # Display daily average wind speed
            st.subheader("Wind speed")

            st.line_chart(
                daily_data.set_index("date")["wind_speed_10m"],
                y_label="Wind speed (km/h)"
            )


            # Display daily average relative humidity
            st.subheader("Relative humidity")

            st.line_chart(
                daily_data.set_index("date")["relative_humidity_2m"],
                y_label="Relative humidity (%)"
            )

        else:

            st.warning("No weather data available.")

else:

    st.info(
        "Select an area and date range, then click "
        "'Download weather data' to get started."
    )
