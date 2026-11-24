import geopandas as gpd
from pathlib import Path

data_folder = Path(__file__).resolve().parent.parent / "data" / "geojson"

# Load the NVE region GeoJSON file
gdf = gpd.read_file(data_folder / "NVE_Region.geojson")

# Display the region codes and names
print("Regions:")
print(gdf[["REGION", "REGIONNAVN"]].to_string(index=False))

# Display the number of geographical areas
print("\nNumber of regions:", len(gdf))

# Display the coordinate reference system
print("CRS:", gdf.crs)