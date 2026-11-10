
import openmeteo_requests
import pandas as pd
import geopandas as gpd
import numpy as np

from pathlib import Path
from shapely.geometry import Point
from openmeteo_requests import Client

# Open-Meteo Archive API
URL = "https://archive-api.open-meteo.com/v1/archive"

# Weather variables to download
HOURLY_VARIABLES = [
    "temperature_2m",
    "precipitation",
    "relative_humidity_2m",
    "wind_speed_10m"
]

# Number of random points per precipitation region
POINTS_PER_REGION = 100

# Map the Streamlit area selector to precipitation regions
REGION_MAPPING = {
    "East": ["RS", "RØ"],
    "North": ["RM", "RN"],
    "West": ["RV"]
}


def find_shapefile(shapefile_path=None):
    """
    Locate NVE_Region.shp.

    You can also provide the full path manually.
    """

    if shapefile_path is not None:
        path = Path(shapefile_path)

        if path.exists():
            return path

        raise FileNotFoundError(
            f"Shapefile not found: {path}"
        )

    # Check common project locations
    project_folder = Path(__file__).resolve().parent

    possible_paths = [
    project_folder / "NVE_Region" / "NVE_Region.shp"
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find NVE_Region.shp. "
        "Please provide the correct shapefile path."
    )




def sample_points(polygon, n=100, seed=42):
    """
    Generate random points inside a polygon.
    """

    rng = np.random.default_rng(seed)

    minx, miny, maxx, maxy = polygon.bounds

    points = []

    # Continue until we have enough points
    while len(points) < n:

        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)

        point = Point(x, y)

        if polygon.covers(point):
            points.append(point)

    return points




def get_region_coordinates(
    region,
    shapefile_path=None,
    points_per_region=POINTS_PER_REGION
):
    """
    Load NVE precipitation regions and generate
    geographical coordinates for the selected area.

    East = RS + RØ
    North = RM + RN
    West = RV

    Returns latitude and longitude coordinates.
    """

    if region not in REGION_MAPPING:
        raise ValueError(
            f"Unknown region: {region}. "
            f"Choose from {list(REGION_MAPPING.keys())}."
        )

    # Find and read shapefile
    path = find_shapefile(shapefile_path)

    gdf = gpd.read_file(path)

    # Check required column
    if "REGION" not in gdf.columns:
        raise ValueError(
            "The shapefile must contain a REGION column."
        )

    # Check coordinate reference system
    if gdf.crs is None:
        raise ValueError(
            "The shapefile has no defined CRS."
        )

    # Select the relevant precipitation regions
    selected_regions = REGION_MAPPING[region]

    selected_gdf = gdf[
        gdf["REGION"].astype(str).str.strip().isin(
            selected_regions
        )
    ].copy()

    if selected_gdf.empty:
        raise ValueError(
            f"No polygons found for {region}: "
            f"{selected_regions}"
        )

    # Combine the selected polygons
    combined_polygon = selected_gdf.geometry.union_all()

    # Generate points in the original CRS
    points = sample_points(
        combined_polygon,
        n=points_per_region * len(selected_regions),
        seed=42
    )

    # Convert points to GeoDataFrame
    points_gdf = gpd.GeoDataFrame(
        geometry=points,
        crs=gdf.crs
    )

    # Convert coordinates to latitude/longitude
    points_gdf = points_gdf.to_crs("EPSG:4326")

    coordinates = []

    for i, point in enumerate(points_gdf.geometry):

        coordinates.append({
            "location_id": i,
            "latitude": point.y,
            "longitude": point.x
        })

    return coordinates


def download_weather(
    region,
    start_date,
    end_date,
    batch_size=10,
    shapefile_path=None
):
    """
    Download hourly meteorological data from Open-Meteo.

    Parameters
    ----------
    region : str
        East, North or West.

    start_date : str
        Start date in YYYY-MM-DD format.

    end_date : str
        End date in YYYY-MM-DD format.

    batch_size : int
        Number of coordinates downloaded per request.

    Returns
    -------
    pandas.DataFrame
        Hourly weather data for all sampled locations.
    """

    # Validate dates
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    if start > end:
        raise ValueError("start_date must be before end_date.")

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    # Get coordinates for selected area
    coordinates = get_region_coordinates(
        region=region,
        shapefile_path=shapefile_path
    )

    # Initialize Open-Meteo client
    openmeteo = Client()

    all_data = []

    # Divide coordinates into batches
    for i in range(0, len(coordinates), batch_size):

        batch = coordinates[i:i + batch_size]

        print(
            f"Downloading {region}: "
            f"{i + 1}-{i + len(batch)} "
            f"of {len(coordinates)} locations"
        )

        # Extract latitude and longitude
        latitudes = [
            location["latitude"] for location in batch
        ]

        longitudes = [
            location["longitude"] for location in batch
        ]

        # API parameters
        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": HOURLY_VARIABLES,
            "models": "era5",
            "timezone": "GMT"
        }

        # Download data
        responses = openmeteo.weather_api(
            URL,
            params=params
        )

        # Process each location
        for location, response in zip(batch, responses):

            hourly = response.Hourly()

            if hourly is None:
                continue

            # Create hourly timestamps
            timestamps = pd.date_range(
                start=pd.to_datetime(
                    hourly.Time(),
                    unit="s",
                    utc=True
                ),
                periods=hourly.Variables(0).ValuesAsNumpy().size,
                freq=pd.Timedelta(
                    seconds=hourly.Interval()
                )
            )

            # Store weather data
            df = pd.DataFrame({
                "date": timestamps,

                "temperature_2m":
                    hourly.Variables(0).ValuesAsNumpy(),

                "precipitation":
                    hourly.Variables(1).ValuesAsNumpy(),

                "relative_humidity_2m":
                    hourly.Variables(2).ValuesAsNumpy(),

                "wind_speed_10m":
                    hourly.Variables(3).ValuesAsNumpy(),

                "location_id":
                    location["location_id"],

                "latitude":
                    location["latitude"],

                "longitude":
                    location["longitude"],

                "region": region
            })

            all_data.append(df)

    # Combine all locations into one DataFrame
    if not all_data:
        return pd.DataFrame()

    weather_data = pd.concat(
        all_data,
        ignore_index=True
    )

    return weather_data



def aggregate_weather_daily(weather_data):
    """
    Aggregate hourly weather data to daily values.

    Precipitation is summed per location per day.
    Other variables are averaged per location per day.

    Finally, values are averaged across locations.
    """

    if weather_data.empty:
        return pd.DataFrame()

    data = weather_data.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        utc=True
    ).dt.floor("D")

    # Aggregate each location separately
    daily = data.groupby(
        ["date", "region", "location_id"]
    ).agg({
        "temperature_2m": "mean",
        "precipitation": "sum",
        "relative_humidity_2m": "mean",
        "wind_speed_10m": "mean"
    }).reset_index()

    # Calculate average across locations
    daily_average = daily.groupby(
        ["date", "region"]
    ).agg({
        "temperature_2m": "mean",
        "precipitation": "mean",
        "relative_humidity_2m": "mean",
        "wind_speed_10m": "mean"
    }).reset_index()

    return daily_average
