
import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd
from pathlib import Path

from functions.water_functions import (
    get_water_data,
    process_water_data,
)

from functions.weather_functions import (
    download_weather,
    aggregate_weather_period
)

@st.cache_data(show_spinner=False)
def get_weather_data_cached():
    """
    Download weather data once for a fixed historical period.
    """

    all_weather = []

    for region in ["East", "North", "West"]:

        weather_data = download_weather(
            region=region,
            start_date="2024-01-01",
            end_date="2025-12-31"
        )

        if not weather_data.empty:
            all_weather.append(weather_data)

    if not all_weather:
        return pd.DataFrame()

    return pd.concat(
        all_weather,
        ignore_index=True
    )


def get_weather_period_data(weather_data, start_date, end_date):
    """
    Aggregate already downloaded weather data for selected dates.
    """

    return aggregate_weather_period(
        weather_data,
        start_date,
        end_date
    )

st.title("Interactive map")

# --------------------------------------------------
# 1. Load GeoJSON files
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

bud_path = BASE_DIR / "data" / "geojson" / "Budområder.geojson"
region_path = BASE_DIR / "data" / "geojson" / "NVE_Region.geojson"

gdf_bud = gpd.read_file(bud_path)
gdf_region = gpd.read_file(region_path)
gdf_region["REGION"] = gdf_region["REGION"].replace({
    "RÃ\x98": "RØ",
    "RÃ˜": "RØ",
    "RØ": "RØ"
})

# --------------------------------------------------
# 2. Get reservoir data from NVE
# --------------------------------------------------

water_df = get_water_data()
water_df = process_water_data(water_df)

# Filter price areas
price_df = water_df[
    water_df["omrType"] == "EL"
].copy()

# Convert date and area number
price_df["Date"] = pd.to_datetime(
    price_df["dato_Id"],
    errors="coerce"
)

price_df["omrnr"] = pd.to_numeric(
    price_df["omrnr"],
    errors="coerce"
)

# Create matching area names
price_df["budomr"] = (
    "NO " + price_df["omrnr"].astype("Int64").astype(str)
)

price_df = price_df.dropna(
    subset=["Date", "omrnr", "fyllingsgrad"]
)


# --------------------------------------------------
# 3. Select date
# --------------------------------------------------

st.subheader("Select date")

min_date = price_df["Date"].min().date()
max_date = price_df["Date"].max().date()

selected_date = st.date_input(
    "Select date",
    value=max_date,
    min_value=min_date,
    max_value=max_date,
    key="price_area_date",
)


# --------------------------------------------------
# 4. Get latest available values for selected date
# --------------------------------------------------

selected_price_df = price_df[
    price_df["Date"].dt.date <= selected_date
].copy()

selected_price_df = (
    selected_price_df
    .sort_values("Date")
    .groupby("omrnr")
    .tail(1)
)

# water values and stuff
# Filter water areas
water_area_df = water_df[
    water_df["omrType"] == "VASS"
].copy()

water_area_df["Date"] = pd.to_datetime(
    water_area_df["dato_Id"],
    errors="coerce"
)

water_area_df["omrnr"] = pd.to_numeric(
    water_area_df["omrnr"],
    errors="coerce"
)

water_area_df = water_area_df.dropna(
    subset=["Date", "omrnr", "fyllingsgrad"]
)

# Select latest available values for selected date
selected_water_df = water_area_df[
    water_area_df["Date"].dt.date <= selected_date
].copy()

selected_water_df = (
    selected_water_df
    .sort_values("Date")
    .groupby("omrnr")
    .tail(1)
)



# --------------------------------------------------
# 5. Merge reservoir values with GeoJSON
# --------------------------------------------------

gdf = gdf_bud.copy()

gdf["budomr"] = gdf["budomr"].astype(str).str.strip()
selected_price_df["budomr"] = (
    selected_price_df["budomr"].astype(str).str.strip()
)

gdf = gdf.merge(
    selected_price_df[["budomr", "fyllingsgrad"]],
    on="budomr",
    how="left"
)

gdf["fyllingsgrad"] = pd.to_numeric(
    gdf["fyllingsgrad"],
    errors="coerce"
).round(2)

# --------------------------------------------------
# 6. Define colors based on reservoir filling
# --------------------------------------------------

def get_color(value):

    if pd.isna(value):
        return [180, 180, 180, 100]

    elif value < 40:
        return [220, 50, 50, 170]

    elif value < 60:
        return [255, 165, 0, 170]

    elif value < 80:
        return [255, 220, 0, 170]

    else:
        return [40, 170, 80, 170]


gdf["fill_color"] = gdf["fyllingsgrad"].apply(get_color)
# --------------------------------------------------
# 7. Select area type
# --------------------------------------------------
# Map the five weather regions to three water areas
region_to_water_area = {
    "RS": "East",
    "RØ": "East",
    "RV": "West",
    "RM": "North",
    "RN": "North",
}

# Create water area GeoDataFrame
gdf_water = gdf_region.copy()

gdf_water["water_area"] = (
    gdf_water["REGION"].map(region_to_water_area)
)

# Merge polygons belonging to the same water area
gdf_water = gdf_water.dissolve(
    by="water_area",
    as_index=False
)

# Match water areas to NVE area numbers
water_area_mapping = {
    "East": 1,
    "West": 2,
    "North": 3,
}

gdf_water["omrnr"] = (
    gdf_water["water_area"].map(water_area_mapping)
)

# Merge reservoir filling values
gdf_water = gdf_water.merge(
    selected_water_df[["omrnr", "fyllingsgrad"]],
    on="omrnr",
    how="left"
)

# Different color for each price area
area_colors = {
    "NO 1": [255, 99, 71, 170],    # Red
    "NO 2": [65, 105, 225, 170],   # Blue
    "NO 3": [50, 205, 50, 170],    # Green
    "NO 4": [255, 165, 0, 170],   # Orange
    "NO 5": [148, 0, 211, 170],   # Purple
}

water_colors = {
    "East": [255, 99, 71, 170],
    "West": [65, 105, 225, 170],
    "North": [50, 205, 50, 170],
}

weather_region_colors = {
    "RS": area_colors["NO 1"],
    "RØ": area_colors["NO 5"],
    "RV": area_colors["NO 2"],
    "RM": area_colors["NO 3"],
    "RN": area_colors["NO 4"],
}


area_type = st.selectbox(
    "Select area type",
    ["Price area", "Water area", "Weather region"],
    key="map_area_type",
)

# Weather settings
if area_type == "Weather region":

    st.subheader("Weather settings")

    col1, col2 = st.columns(2)

    with col1:
        weather_start_date = st.date_input(
            "Start date",
            value=pd.to_datetime("2025-01-01").date(),
            key="weather_start_date"
        )

    with col2:
        weather_end_date = st.date_input(
            "End date",
            value=pd.to_datetime("2025-01-07").date(),
            key="weather_end_date"
        )

    weather_parameter = st.selectbox(
        "Select weather property",
        [
            "Temperature",
            "Precipitation",
            "Relative humidity",
            "Wind speed"
        ],
        key="weather_parameter"
    )

    if weather_start_date > weather_end_date:
        st.error("Start date must be before end date.")
        st.stop()

    # Download weather data (cached)
    with st.spinner("Loading weather data..."):
        weather_df = get_weather_data_cached()

    # Aggregate based on selected dates
    weather_period = get_weather_period_data(
        weather_df,
        weather_start_date,
        weather_end_date
    )
# --------------------------------------------------
# 9. Create map layer
# --------------------------------------------------

if area_type == "Price area":

    gdf = gdf_bud.copy()

    gdf = gdf.merge(
        selected_price_df[["budomr", "fyllingsgrad"]],
        on="budomr",
        how="left"
    )

    gdf["fill_color"] = gdf["budomr"].map(area_colors)

    id_column = "budomr"


elif area_type == "Water area":

    gdf = gdf_water.copy()

    gdf["fill_color"] = gdf["water_area"].map(water_colors)

    id_column = "water_area"


else:

    gdf = gdf_region.copy()

    id_column = "REGION"

    if weather_period.empty:
        st.warning("No weather data available for the selected period.")

    else:

        # Map each weather region to its corresponding NVE region codes
        region_mapping = {
            "East": ["RS", "RØ"],
            "North": ["RM", "RN"],
            "West": ["RV"]
        }

        # Select the weather variable
        parameter_mapping = {
            "Temperature": "temperature_2m",
            "Precipitation": "precipitation",
            "Relative humidity": "relative_humidity_2m",
            "Wind speed": "wind_speed_10m"
        }

        selected_parameter = parameter_mapping[
            weather_parameter
        ]

        # Create mapping from NVE region to aggregated weather values
        weather_lookup = {}

        for _, row in weather_period.iterrows():

            weather_region = row["region"]
            value = row[selected_parameter]

            for nve_region in region_mapping[weather_region]:
                weather_lookup[nve_region] = value

        gdf["weather_value"] = gdf["REGION"].map(
            weather_lookup
        )

        # Create colors based on weather values
        values = gdf["weather_value"].dropna()

        if not values.empty:

            min_value = values.min()
            max_value = values.max()

            def get_weather_color(value):

                if pd.isna(value):
                    return [180, 180, 180, 100]

                if max_value == min_value:
                    normalized = 0.5
                else:
                    normalized = (
                        (value - min_value) /
                        (max_value - min_value)
                    )

                # Blue for low values, red for high values
                red = int(255 * normalized)
                blue = int(255 * (1 - normalized))

                return [red, 80, blue, 170]

            gdf["fill_color"] = gdf["REGION"].map(
                weather_region_colors
            )

        else:
            gdf["fill_color"] = [
                [180, 180, 180, 100]
            ] * len(gdf)



# 8. Initialize session state
# --------------------------------------------------

if "map_selected_area" not in st.session_state:
    st.session_state["map_selected_area"] = None

if "map_selected_area_type" not in st.session_state:
    st.session_state["map_selected_area_type"] = None


# --------------------------------------------------
# 9. Create map layer
# --------------------------------------------------
if area_type in ["Price area", "Water area"]:

    gdf["fyllingsgrad_visning"] = gdf["fyllingsgrad"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )

elif area_type == "Weather region":

    gdf["weather_value_visning"] = gdf["weather_value"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )

geojson_data = gdf.__geo_interface__


layer = pdk.Layer(
    "GeoJsonLayer",
    id="area-layer",
    data=geojson_data,
    stroked=True,
    filled=True,
    get_fill_color="properties.fill_color",
    get_line_color=[255, 255, 255, 255],
    get_line_width=3,
    line_width_min_pixels=2,
    pickable=True,
    auto_highlight=True,
)


# --------------------------------------------------
# 10. Create map
# --------------------------------------------------
# --------------------------------------------------
# Tooltip
# --------------------------------------------------

if area_type == "Price area":

    tooltip_text = (
        "{budomr}\n"
        "Reservoir filling: {fyllingsgrad_visning}%"
    )

elif area_type == "Water area":

    tooltip_text = (
        "{water_area}\n"
        "Reservoir filling: {fyllingsgrad_visning}%"
    )

else:

    unit_mapping = {
        "Temperature": "°C",
        "Precipitation": "mm",
        "Relative humidity": "%",
        "Wind speed": "km/h"
    }

    tooltip_text = (
        "{REGION}\n"
        + weather_parameter
        + ": {weather_value_visning}"
        + " "
        + unit_mapping[weather_parameter]
    )   

view_state = pdk.ViewState(
    latitude=64.5,
    longitude=15,
    zoom=3.5,
    pitch=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style=None,
    tooltip={
    "text": tooltip_text
    },
)

event = st.pydeck_chart(
    deck,
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-object",
)

if area_type == "Weather region" and not weather_period.empty:

    st.subheader("Aggregated weather properties")

    st.dataframe(
        weather_period,
        use_container_width=True
    )
# --------------------------------------------------
# 11. Handle map selection
# --------------------------------------------------

if event and event.selection:

    objects = event.selection.get("objects", {})
    selected_objects = objects.get("area-layer", [])

    if selected_objects:

        selected_area = selected_objects[0]["properties"][id_column]

        st.session_state["map_selected_area"] = selected_area
        st.session_state["map_selected_area_type"] = area_type


# --------------------------------------------------
# 12. Display selected area
# --------------------------------------------------

st.write(
    "Selected area:",
    st.session_state["map_selected_area"],
)

st.write(
    "Selected area type:",
    st.session_state["map_selected_area_type"],
)
