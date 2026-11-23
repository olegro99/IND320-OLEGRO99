import geopandas as gpd
from pathlib import Path

# Define the project and data folders
project_folder = Path(__file__).resolve().parent.parent
data_folder = project_folder / "data"
output_folder = data_folder / "geojson"

output_folder.mkdir(parents=True, exist_ok=True)

# Find all shapefiles
shapefiles = list(data_folder.rglob("*.shp"))

print("Data folder:", data_folder)
print("Found shapefiles:", [file.name for file in shapefiles])

for shapefile in shapefiles:

    # Read shapefile
    gdf = gpd.read_file(shapefile)

    # Ensure that the coordinate reference system is defined
    if gdf.crs is None:
        raise ValueError(f"Missing CRS: {shapefile}")

    # Convert coordinates to WGS84 (latitude/longitude)
    gdf = gdf.to_crs(epsg=4326)

    # Define output filename
    output_file = output_folder / f"{shapefile.stem}.geojson"

    # Export as GeoJSON
    gdf.to_file(output_file, driver="GeoJSON")

    print(f"Converted: {shapefile.name} -> {output_file}")
