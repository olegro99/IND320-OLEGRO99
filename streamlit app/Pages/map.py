
import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
from pathlib import Path
import json

from functions.download_entsoe_prices import download_entsoe_prices, get_price_values_for_date
from functions.water_functions import get_water_values

# Import the weather functions if they are available.
# This allows the map to work even if the weather module cannot be imported.
try:
    from functions.weather_functions import download_weather, aggregate_weather_daily
    WEATHER_FUNCTIONS_AVAILABLE = True
except ImportError:
    WEATHER_FUNCTIONS_AVAILABLE = False


st.title("Geographical Areas")


# ---------------------------------------------------------------------------
# Store the selected geographical area in Streamlit's session state.
# Session state keeps these values available when the user navigates
# between pages or when Streamlit reruns the application.
# ---------------------------------------------------------------------------

if "selected_area_id" not in st.session_state:
    st.session_state["selected_area_id"] = None

if "selected_area_properties" not in st.session_state:
    st.session_state["selected_area_properties"] = None

if "selected_area_category" not in st.session_state:
    st.session_state["selected_area_category"] = None

# Store downloaded weather data between Streamlit reruns.
if "weather_cache" not in st.session_state:
    st.session_state["weather_cache"] = {}


# ---------------------------------------------------------------------------
# Configuration of geographical identifiers and data columns.
# These settings define how the geographical areas are matched with
# the corresponding price, water and weather data.
# ---------------------------------------------------------------------------

# Column containing the identifiers for the Norwegian price areas (NO 1–NO 5).
PRICE_ID_COLUMN = "budomr"

# Column containing the geographical region codes used for weather data.
REGION_COLUMN = "REGION"

# Translate the original NVE region codes into the larger regions
# used by the weather functions.
REGION_GROUPS = {
    "RS": "East",
    "RØ": "East",
    "RM": "North",
    "RN": "North",
    "RV": "West",
}

# Connect the weather properties shown in the selector to the column names
# expected in the aggregated weather dataset.
WEATHER_PROPERTY_COLUMNS = {
    "Temperature": "temperature_2m",
    "Precipitation": "precipitation",
    "Relative humidity": "relative_humidity_2m",
    "Wind speed": "wind_speed_10m",
}


# Locate the folder containing the GeoJSON files.
geojson_folder = Path(__file__).resolve().parent.parent / "data" / "geojson"


# ---------------------------------------------------------------------------
# User selections.
# The selected options determine which dataset is retrieved and displayed.
# ---------------------------------------------------------------------------

# Let the user choose which type of information should be shown on the map.
display_option = st.selectbox(
    "Colour areas by",
    ["Price area", "Water area", "Weather property"]
)

# Only display the weather variable selector when weather data is selected.
if display_option == "Weather property":
    weather_property = st.selectbox(
        "Select weather property",
        list(WEATHER_PROPERTY_COLUMNS.keys())
    )
else:
    weather_property = None


# ---------------------------------------------------------------------------
# Select the time period used to retrieve and aggregate the data.
# Electricity prices are retrieved for one specific day, while water and
# weather data are aggregated over a user-defined period.
# ---------------------------------------------------------------------------

if display_option == "Price area":
    selected_date = st.date_input("Select date")

    # Use the same date as both the start and end of the selected period.
    period_start, period_end = selected_date, selected_date

else:
    st.caption("Select the period to aggregate over:")

    # Display the start and end date selectors side by side.
    col1, col2 = st.columns(2)

    with col1:
        period_start = st.date_input("Start date", key="period_start")

    with col2:
        period_end = st.date_input("End date", key="period_end")

    # Make sure the selected period has a valid date range.
    if period_end < period_start:
        st.error("End date must be on or after the start date.")
        st.stop()


# ---------------------------------------------------------------------------
# Find the available GeoJSON files.
# Each file contains the geographical boundaries and attributes
# needed to display a specific type of area on the map.
# ---------------------------------------------------------------------------

geojson_files = list(geojson_folder.glob("*.geojson"))

# Stop the application if the GeoJSON folder does not contain any files.
if not geojson_files:
    st.warning("No GeoJSON files found.")
    st.stop()

# Create a dictionary where each file name is linked to its file path.
area_options = {file.stem: file for file in geojson_files}


@st.cache_data
def get_geojson_columns(path_str: str) -> list[str]:
    """
    Read the column names from a GeoJSON file.

    Cache the result so that the same file does not need to be read
    repeatedly every time Streamlit reruns the application.
    The returned columns are used to check which files can be selected.
    """
    tmp = gpd.read_file(path_str)
    return list(tmp.columns)


# ---------------------------------------------------------------------------
# Select a suitable geographical dataset.
# For price mapping, the GeoJSON file must contain the 'budomr' column,
# since this column identifies the price areas used by ENTSO-E.
# Other display modes currently allow all available GeoJSON files.
# ---------------------------------------------------------------------------

if display_option == "Price area":

    # Keep only GeoJSON files containing the required price area identifier.
    compatible_options = {
        name: path for name, path in area_options.items()
        if PRICE_ID_COLUMN in get_geojson_columns(str(path))
    }

    # Stop if none of the available files contain the required identifier.
    if not compatible_options:
        st.error(
            "No GeoJSON file with a 'budomr' column is available "
            "for price mapping."
        )
        st.stop()

    display_area_options = compatible_options

else:
    display_area_options = area_options


# Let the user choose which geographical boundaries should be displayed.
selected_area = st.selectbox(
    "Select area type (geometry)",
    options=list(display_area_options.keys())
)

# Load the selected GeoJSON file as a GeoDataFrame.
geojson_path = display_area_options[selected_area]
gdf = gpd.read_file(geojson_path)


# Check whether the selected GeoJSON file contains the columns
# required for price mapping and weather mapping.
id_column_is_real_budomr = PRICE_ID_COLUMN in gdf.columns
has_region_column = REGION_COLUMN in gdf.columns


# Choose an identifier for each geographical area.
# Use the actual price area identifier when available.
# Otherwise, create an identifier based on the row index.
if id_column_is_real_budomr:
    effective_id_col = PRICE_ID_COLUMN
else:
    effective_id_col = "_row_id"
    gdf[effective_id_col] = gdf.index.astype(str)


# ---------------------------------------------------------------------------
# Retrieve electricity prices from ENTSO-E.
# The returned values are matched to the geographical areas using
# their price area identifiers (NO 1–NO 5).
# ---------------------------------------------------------------------------

def get_prices_for_map_date(date_str: str, api_key: str) -> dict:
    """
    Download day-ahead electricity prices for the selected date.

    The downloaded data is passed to get_price_values_for_date(),
    which calculates the average price for each price area.

    Returns a dictionary with price area identifiers as keys
    and their corresponding average prices as values.
    """

    # Define the start and end of the selected day for the API request.
    start = pd.to_datetime(date_str).strftime("%Y-%m-%d")
    end = (pd.to_datetime(date_str) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        prices_df = download_entsoe_prices(start, end, api_key)
    except ValueError:
        return {}

    # Calculate the average electricity price for each price area.
    return get_price_values_for_date(prices_df, date_str, agg="mean")


def get_price_area_values(gdf: gpd.GeoDataFrame, selected_date) -> pd.Series:
    """
    Retrieve electricity prices and match them to the geographical areas.

    The 'budomr' column is used to connect each polygon to its
    corresponding electricity price area.
    """

    # Price mapping requires the 'budomr' identifier in the GeoJSON file.
    if not id_column_is_real_budomr:
        st.warning(
            "⚠️ The selected GeoJSON file has no 'budomr' column. "
            "Select 'Budområder' under 'Select area type' to see prices."
        )
        return pd.Series([float("nan")] * len(gdf), index=gdf.index)

    # Retrieve the ENTSO-E API key from Streamlit secrets.
    api_key = st.secrets.get("ENTSOE_API_KEY")

    if not api_key:
        st.error("❌ ENTSOE_API_KEY is missing from secrets.toml.")
        return pd.Series([float("nan")] * len(gdf), index=gdf.index)

    # Download the prices for the selected date.
    price_lookup = get_prices_for_map_date(str(selected_date), api_key)

    if not price_lookup:
        st.warning("⚠️ No prices could be retrieved for the selected date.")
        return pd.Series([float("nan")] * len(gdf), index=gdf.index)

    # Match each geographical area to its electricity price using 'budomr'.
    mapped = gdf[PRICE_ID_COLUMN].map(price_lookup)

    # Identify areas for which no matching price was found.
    missing = gdf.loc[mapped.isna(), PRICE_ID_COLUMN].tolist()

    if missing:
        st.caption(f"Missing prices for: {', '.join(missing)}")

    return mapped


# ---------------------------------------------------------------------------
# Water area values from NVE Magasinstatistikk.
# A matching identifier between the GeoJSON file and the NVE dataset
# must be available before the values can be connected to the map.
# ---------------------------------------------------------------------------

def get_water_values(gdf: gpd.GeoDataFrame) -> pd.Series:

    # Check whether a valid join column has been identified.
    if WATER_JOIN_COLUMN is None or WATER_JOIN_COLUMN not in gdf.columns:
        st.info(
            "ℹ️ Water area colouring requires a verified join between the "
            "NVE Magasinstatistikk 'area_number' field and a matching "
            "column in this GeoJSON file. No such column has been "
            "confirmed yet, so all areas are shown as missing data."
        )
        return pd.Series([float("nan")] * len(gdf), index=gdf.index)

    # NVE data can be connected here once the correct join column is verified.
    return pd.Series([float("nan")] * len(gdf), index=gdf.index)


# ---------------------------------------------------------------------------
# Retrieve and aggregate weather data.
# The original NVE region codes are translated into the larger regions
# used by the existing weather functions before the values are matched
# back to the geographical areas.
# ---------------------------------------------------------------------------

def get_weather_values(gdf: gpd.GeoDataFrame, property_label: str,
                        start_date, end_date) -> pd.Series:

    # Create a default result containing missing values for every area.
    nan_series = pd.Series([float("nan")] * len(gdf), index=gdf.index)

    # Check whether the weather functions were imported successfully.
    if not WEATHER_FUNCTIONS_AVAILABLE:
        st.info(
            "ℹ️ functions.weather_functions could not be imported - "
            "weather colouring is unavailable."
        )
        return nan_series

    # Weather mapping requires the original NVE region codes.
    if not has_region_column:
        st.info(
            f"ℹ️ Weather colouring needs a '{REGION_COLUMN}' column "
            "(found in NVE_Region.geojson). Select that file under "
            "'Select area type' to see weather data."
        )
        return nan_series

    # Find the dataset column corresponding to the selected weather property.
    column_name = WEATHER_PROPERTY_COLUMNS.get(property_label)

    # Get the region codes present in the selected GeoJSON file.
    raw_codes = gdf[REGION_COLUMN].unique()

    # Translate the original region codes into the larger weather regions.
    groups_needed = sorted({
        REGION_GROUPS[c] for c in raw_codes if c in REGION_GROUPS
    })

    # Identify region codes that are not included in the mapping dictionary.
    unmapped = [c for c in raw_codes if c not in REGION_GROUPS]

    if unmapped:
        st.caption(f"⚠️ Unmapped REGION codes (no data shown): {unmapped}")

    # Stop if none of the region codes could be matched to a weather region.
    if not groups_needed:
        st.warning("⚠️ No recognised REGION codes found - check REGION_GROUPS mapping.")
        return nan_series

    # Store the aggregated weather value for each larger region.
    group_values = {}

    for group in groups_needed:
        try:
            # Create a cache key based on region and selected dates.
            cache_key = (
                group,
                str(start_date),
                str(end_date)
            )

            # Retrieve previously downloaded weather data.
            daily = st.session_state["weather_cache"].get(cache_key)

            if daily is None:
                st.info(
                    f"Weather data for {group} is not downloaded yet. "
                    "Click 'Download weather data' to retrieve it."
                )
                continue

            # Calculate the average value over the selected time period.
            group_values[group] = daily[column_name].mean()

        except Exception as e:
            st.warning(f"⚠️ Weather download/aggregation failed for region '{group}': {e}")

    # Return missing values if no weather data could be retrieved.
    if not group_values:
        return nan_series

    # Match each original NVE region code to its aggregated weather value.
    def lookup(raw_code):
        group = REGION_GROUPS.get(raw_code)
        return group_values.get(group, float("nan"))

    return gdf[REGION_COLUMN].apply(lookup)


# ---------------------------------------------------------------------------
# Download weather data only when the user presses the button.
# Previously downloaded data is stored in session state.
# ---------------------------------------------------------------------------

if display_option == "Weather property" and WEATHER_FUNCTIONS_AVAILABLE:

    if st.button("Download weather data", type="primary"):

        # Identify the weather regions needed for the selected GeoJSON.
        if has_region_column:

            groups_needed = sorted({
                REGION_GROUPS[c]
                for c in gdf[REGION_COLUMN].unique()
                if c in REGION_GROUPS
            })

            # Download data for each required region.
            for group in groups_needed:

                cache_key = (
                    group,
                    str(period_start),
                    str(period_end)
                )

                with st.spinner(f"Downloading weather data for {group}..."):

                    try:
                        raw = download_weather(
                            group,
                            str(period_start),
                            str(period_end)
                        )

                        if raw is None or raw.empty:
                            st.warning(
                                f"No weather data returned for {group}."
                            )
                            continue

                        # Aggregate the downloaded data by day.
                        daily = aggregate_weather_daily(raw)

                        # Save the aggregated data in session state.
                        st.session_state["weather_cache"][cache_key] = daily

                    except Exception as e:
                        st.error(
                            f"Weather download failed for {group}: {e}"
                        )

            st.success("Weather data download completed.")

        else:
            st.warning(
                "Select a GeoJSON file containing the REGION column."
            )

# ---------------------------------------------------------------------------
# Select the correct data retrieval function based on the user's choice.
# All functions return a Series with one value for each geographical area.
# ---------------------------------------------------------------------------

def get_values_for_areas(gdf, display_option, weather_property,
                          period_start, period_end) -> pd.Series:

    if display_option == "Price area":
        return get_price_area_values(gdf, period_start)

    elif display_option == "Water area":
        return get_water_values(gdf)

    elif display_option == "Weather property":
        return get_weather_values(gdf, weather_property, period_start, period_end)

    return pd.Series([float("nan")] * len(gdf), index=gdf.index)


# Retrieve the values for the selected data type and add them to the GeoDataFrame.
gdf["value"] = get_values_for_areas(
    gdf, display_option, weather_property, period_start, period_end
)


# ---------------------------------------------------------------------------
# Convert the retrieved values into colours for the map.
# Areas with missing values are displayed using a transparent grey colour.
# Areas with valid values are coloured according to their relative values.
# ---------------------------------------------------------------------------

def value_to_color(value, min_val, max_val, alpha=120):

    # Use grey when no data is available for the geographical area.
    if pd.isna(value):
        return [180, 180, 180, 60]

    # Scale the value between 0 and 1 based on the minimum and maximum values.
    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        ratio = 0.0
    else:
        ratio = (value - min_val) / (max_val - min_val)

    # Keep the colour scale within the valid range.
    ratio = max(0.0, min(1.0, ratio))

    # Create a colour gradient from yellow (low values) to red (high values).
    r = 255
    g = int(255 * (1 - ratio))
    b = 60

    return [r, g, b, alpha]


# Find the minimum and maximum available values to define the colour scale.
valid_values = gdf["value"].dropna()

min_val = valid_values.min() if not valid_values.empty else float("nan")
max_val = valid_values.max() if not valid_values.empty else float("nan")

# Assign a fill colour to each geographical area based on its value.
gdf["fill_color"] = gdf["value"].apply(
    lambda v: value_to_color(v, min_val, max_val)
)


# ---------------------------------------------------------------------------
# Highlight the geographical area selected by the user.
# The selected area receives a thicker red outline, while the other
# areas keep their standard outline colour and width.
# ---------------------------------------------------------------------------

def get_line_color(area_id):

    if area_id == st.session_state["selected_area_id"]:
        return [255, 0, 0, 255]

    return [30, 90, 150, 200]


def get_line_width(area_id):

    if area_id == st.session_state["selected_area_id"]:
        return 5

    return 1


# Add outline colours and widths to the GeoDataFrame.
gdf["line_color"] = gdf[effective_id_col].apply(get_line_color)
gdf["line_width"] = gdf[effective_id_col].apply(get_line_width)


# ---------------------------------------------------------------------------
# Prepare the geographical data for PyDeck.
# Convert the GeoDataFrame into GeoJSON and calculate the map centre
# using the geographical boundaries of the selected dataset.
# ---------------------------------------------------------------------------

geojson_data = json.loads(gdf.to_json())

# Calculate the centre coordinates from the dataset's bounding box.
min_lon, min_lat, max_lon, max_lat = gdf.total_bounds

center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2


# Create a GeoJSON layer containing the geographical polygons.
# The colour and outline properties are read from each feature's attributes.
geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    id="area-layer",
    data=geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    extruded=False,
    get_fill_color="properties.fill_color",
    get_line_color="properties.line_color",
    get_line_width="properties.line_width",
    line_width_min_pixels=1,
)


# Set the initial map position using the calculated centre coordinates.
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=5,
    pitch=0,
)


# Create the map and define the information displayed when hovering over an area.
deck = pdk.Deck(
    layers=[geojson_layer],
    initial_view_state=view_state,
    tooltip={"text": "Value: {value}"},
)


# Display the interactive map.
# on_select="rerun" makes Streamlit rerun the page when an area is selected.
# selection_mode="single-object" allows the user to select one area at a time.
event = st.pydeck_chart(
    deck,
    use_container_width=True,
    height=650,
    key="area_map",
    on_select="rerun",
    selection_mode="single-object",
)


# ---------------------------------------------------------------------------
# Handle the user's map selection.
# Retrieve the clicked polygon, store its identifier and attributes in
# session state, and rerun the page so that the selected area is highlighted.
# Other pages can access the stored information through st.session_state.
# ---------------------------------------------------------------------------

if event is not None:
    selection = getattr(event, "selection", None)

    if selection:
        # Get the index of the selected feature in the map layer.
        indices = selection.get("indices", {})
        layer_indices = indices.get("area-layer", [])

        if layer_indices:
            clicked_idx = layer_indices[0]

            # Retrieve the corresponding row from the GeoDataFrame.
            clicked_row = gdf.iloc[clicked_idx]
            clicked_id = clicked_row[effective_id_col]

            # Update the stored selection only if a different area was clicked.
            if clicked_id != st.session_state["selected_area_id"]:
                st.session_state["selected_area_id"] = clicked_id

                # Store the selected area's attributes, excluding its geometry.
                st.session_state["selected_area_properties"] = (
                    clicked_row.drop(labels=["geometry"], errors="ignore").to_dict()
                )

                # Store which data category was active when the area was selected.
                st.session_state["selected_area_category"] = display_option

                # Rerun the page to update the outline of the selected area.
                st.rerun()


# Display the identifier of the currently selected geographical area.
if st.session_state["selected_area_id"] is not None:
    st.caption(
        f"Selected area ({st.session_state['selected_area_category']}): "
        f"{st.session_state['selected_area_id']}"
    )
