import json
import geopandas as gpd
import streamlit as st
import plotly.express as px
import sys
from pathlib import Path



from functions.water_functions import get_water_values, process_water_data, get_water_data


# --- Load GeoJSON as GeoDataFrame ---
HERE = Path(__file__).resolve().parent  # .../streamlit app/Pages

GEOJSON_WATER = (HERE.parent / "data" / "geojson" / "NVE_Region.geojson")
gdf_water = gpd.read_file(str(GEOJSON_WATER))

st.write("Kolonner i gdf_water:", gdf_water.columns.tolist())
st.dataframe(gdf_water.head(5))
# etter at du kaller funksjonen og lagrer resultatet:
# Mapping: VASS omrnr -> GeoJSON region-kode (REGION)
# (du bekreftet dette)
vass_to_region = {
    1: "RN",  # Nord
    2: "RØ",  # Øst
    3: "RV",  # Vest
}

# Vi lager en hjelpekode: regionkode -> VASS-omrnr
region_to_vass = {reg: omrnr for omrnr, reg in vass_to_region.items()}

# --- UI: velg periode ---
st.caption("Velg periode som skal aggregeres over")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Startdato", value=None)
with col2:
    end_date = st.date_input("Sluttdato", value=None)

agg_func = st.selectbox("Aggregering", ["mean", "min", "max", "last"], index=0)

if start_date is None or end_date is None:
    st.warning("Velg start- og sluttdato først.")
    st.stop()

# --- Hent vannverdier for VASS ---
# Her trenger vi at get_water_values returnerer verdier per VASS-område (omrnr).
# Siden get_water_values i din kode sannsynligvis lager budomr, må vi i stedet:
# - hente VASS data (omrnr) fra API via water_functions
# Hvis get_water_values IKKE støtter omrnr direkte, må vi justere water_functions.
gdf_water = gdf_water.copy()

# cast OBJECTID til string slik at den matcher omrnr_std (som er str i agg_df)
gdf_water["OBJECTID"] = gdf_water["OBJECTID"].astype(str)
# For nå: vi forsøker å bruke samme get_water_values, men med id_col_geo="omrnr"
# og forventer at water_functions kan bruke omrnr som id.
water_gdf = get_water_values(
    gdf=gdf_water,
    start_date=start_date,
    end_date=end_date,
    agg_func=agg_func,          
    id_col_geo="OBJECTID",
    value_col="fyllingsgrad",   
)

values_gdf_or_df = water_gdf



# ---- Hvis get_water_values ikke gir omrnr: vi må bruke en fallback
# Vi sjekker hva slags ID-kolonne vi faktisk fikk:
print("Kolonner i water_gdf:", water_gdf.columns.tolist())

# For plot trenger vi match mot GeoJSON sin REGION.
# Vi bygger en value per REGION ved å mappe fra VASS-omrnr til REGION.
# (Her må water_gdf inneholde kolonnen 'omrnr')
if "omrnr" not in water_gdf.columns:
    st.error(
        "water_gdf mangler kolonnen 'omrnr'. "
        "Da må vi endre water_functions.py slik at get_water_values kan returnere VASS-verdier per omrnr."
    )
    st.stop()

# Bygg plot-tabell per GeoJSON region
water_gdf["REGION"] = water_gdf["omrnr"].map(vass_to_region)

df_plot = water_gdf.dropna(subset=["REGION"])[["REGION", "fyllingsgrad"]].copy()

# --- Konverter GeoDataFrame til GeoJSON for Plotly ---
geojson_obj = json.loads(gdf_water.to_json())

# Fargen skal kobles på GeoJSON sin property for region
# I din GeoJSON har du REGIONSOM FELT: gdf_water["REGION"].
featureidkey = "properties.REGION"

fig = px.choropleth_map(
    df_plot,
    geojson=geojson_obj,
    locations="REGION",
    featureidkey=featureidkey,
    color="fyllingsgrad",
    map_style="open-street-map",
    zoom=6,
    center={"lat": 63.4, "lon": 10.4},
)

fig.update_traces(marker_line=dict(width=1.0, color="rgba(255,255,255,0.9)"))

# --- Marker valgt område med tykk outline ---
selected = st.session_state.get("selected_area")
if selected is not None:
    sel_df = df_plot[df_plot["REGION"] == selected].copy()

    if not sel_df.empty:
        custom_scale_selected = [
            (0.0, "rgba(0,0,0,0.0)"),
            (1.0, "rgba(0,0,0,0.0)"),
        ]

        fig_sel = px.choropleth_map(
            sel_df,
            geojson=geojson_obj,
            locations="REGION",
            featureidkey="properties.REGION",
            color="fyllingsgrad",
            color_continuous_scale=custom_scale_selected,
            map_style="open-street-map",
            zoom=6,
            center={"lat": 63.4, "lon": 10.4},
        )
        fig_sel.update_traces(marker_line=dict(width=5.0, color="rgba(255, 0, 0, 1.0)"))

        for tr in fig_sel.data:
            fig.add_trace(tr)

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# --- Klikk-handling ---
# Vi må hente hva Plotly returnerer ved click.
# Siden dette kan variere med Streamlit/Plotly-versjon:
# - vi bruker en debug-expander
st.caption("Klikk et område for å markere det ✅")

clicked_payload = st.plotly_chart(
    fig,
    key="water_map",
    on_select="rerun",
    use_container_width=True,
)

with st.expander("Debug: click payload (må sjekkes første gang) 🧪"):
    st.write(st.session_state.get("water_map"))
    st.write("selected_area:", st.session_state.get("selected_area"))

# --- OBS: fyll inn riktig mapping etter at du ser payload ---
# Vanligvis vil du kunne gjøre noe som dette (tilpass etter payload-strukturen):
#
# payload = st.session_state.get("water_map")
# if payload and "points" in payload and len(payload["points"]) > 0:
#     st.session_state["selected_area"] = payload["points"][0]["location"]
#
# For at jeg skal skrive riktig linje: send meg outputet fra debug-expander.
