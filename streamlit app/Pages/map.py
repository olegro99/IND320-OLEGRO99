
import streamlit as st
import geopandas as gpd
import pydeck as pdk
from pathlib import Path
import json

st.title("Geographical Areas")

# Locate the GeoJSON folder
geojson_folder = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "geojson"
)

# Find available GeoJSON files
geojson_files = list(geojson_folder.glob("*.geojson"))

if not geojson_files:
    st.warning("No GeoJSON files found.")
    st.stop()

# Create a dictionary of available area types
area_options = {
    file.stem: file for file in geojson_files
}

# Let the user select an area type
selected_area = st.selectbox(
    "Select area type",
    options=list(area_options.keys())
)

# Load the selected GeoJSON file
geojson_path = area_options[selected_area]

with open(geojson_path, encoding="utf-8") as f:
    geojson_data = json.load(f)

# Read the GeoJSON with GeoPandas to calculate map boundaries
gdf = gpd.read_file(geojson_path)

# Calculate the center of the selected geographical area
min_lon, min_lat, max_lon, max_lat = gdf.total_bounds

center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2

# Create a GeoJSON layer
geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    extruded=False,
    get_fill_color=[80, 160, 220, 70],
    get_line_color=[30, 90, 150, 200],
    line_width_min_pixels=1
)

# Configure map view
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=5,
    pitch=0
)

# Create interactive map
deck = pdk.Deck(
    layers=[geojson_layer],
    initial_view_state=view_state,
    tooltip={"text": "Geographical area"}
)

# Display map
st.pydeck_chart(
    deck,
    use_container_width=True,
    height=650
)
