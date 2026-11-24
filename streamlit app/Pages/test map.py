from functions.water_functions import get_water_values
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import sys

# 📂 Finn prosjektrot (streamlit app/) uansett hvor filen kjøres fra
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" / "geojson"
PRICE_AREA_FILE = DATA_DIR / "Budområder.geojson"
NVE_REGION_FILE = DATA_DIR / "NVE_Region.geojson"

st.set_page_config(layout="wide")
st.title("🗺️ Test kart")

# 🎛️ Selector
area_type = st.selectbox(
    "Velg visning",
    ["Price area", "Water area", "Weather property"]
)

# 📥 Last inn GeoJSON
@st.cache_data
def load_geojson(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

if area_type == "Price area":
    gdf = load_geojson(PRICE_AREA_FILE)
elif area_type == "Water area":
    gdf = load_geojson(NVE_REGION_FILE)  # ⚠️ antagelse
else:
    gdf = load_geojson(PRICE_AREA_FILE)  # ⚠️ placeholder

st.write(f"Viser {len(gdf)} områder fra **{area_type}**")
st.write("Kolonner:", list(gdf.columns))

# 🗺️ Enkelt kart uten farger ennå
m = folium.Map(location=[65, 15], zoom_start=4)
folium.GeoJson(gdf).add_to(m)

st_folium(m, width=1000, height=600)
# I test map.py, når area_type == "Water area":
gdf = load_geojson(PRICE_AREA_FILE)  # 👈 Budområder, IKKE NVE_Region!
merged = get_water_values(
    gdf,
    start_date="2024-01-01",
    end_date="2024-01-31",
    agg_func="mean",
    value_col="fyllingsgrad",
    id_col_geo="budomr",
)
st.write(merged[["budomr", "fyllingsgrad"]])

