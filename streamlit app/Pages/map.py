
import streamlit as st
import geopandas as gpd
import pydeck as pdk
from pathlib import Path
import json

st.title("Geographical Areas")

# Define the path to the folder containing the GeoJSON files
geojson_folder = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "geojson"
)

# Find all available GeoJSON files in the folder
geojson_files = list(geojson_folder.glob("*.geojson"))

# Stop execution if no GeoJSON files are found
if not geojson_files:
    st.warning("No GeoJSON files found.")
    st.stop()

# Create a dictionary linking area names to their corresponding file paths
area_options = {
    file.stem: file for file in geojson_files
}

# Allow the user to select which geographical area to display
selected_area = st.selectbox(
    "Select area type",
    options=list(area_options.keys())
)

# Get the file path corresponding to the selected area
geojson_path = area_options[selected_area]

# Load the GeoJSON data from the selected file
with open(geojson_path, encoding="utf-8") as f:
    geojson_data = json.load(f)

# Read the GeoJSON file with GeoPandas to access its geographical data
# and calculate the map boundaries
gdf = gpd.read_file(geojson_path)

# Calculate the minimum and maximum longitude and latitude
# to determine the geographical boundaries of the map
min_lon, min_lat, max_lon, max_lat = gdf.total_bounds

# Calculate the centre coordinates of the selected geographical area
center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2

# Create a GeoJSON layer containing the geographical areas
geojson_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_data,
    pickable=True,  # Enable interaction with the geographical areas
    stroked=True,   # Display outlines around the areas
    filled=True,    # Fill the areas with colour
    extruded=False, # Display the areas as flat polygons
    get_fill_color=[80, 160, 220, 70],   # Set the fill colour and transparency
    get_line_color=[30, 90, 150, 200],   # Set the outline colour
    line_width_min_pixels=1              # Set the minimum outline width
)

# Configure the initial map view using the calculated centre coordinates
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=5,
    pitch=0
)

# Create the map and configure the layer and tooltip
deck = pdk.Deck(
    layers=[geojson_layer],
    initial_view_state=view_state,
    tooltip={"text": "Geographical area"}
)

# Display the interactive map in Streamlit
st.pydeck_chart(
    deck,
    use_container_width=True,
    height=650
)
