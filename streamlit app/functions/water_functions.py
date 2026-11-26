import requests
import pandas as pd
import geopandas as gpd

URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"


def get_water_data() -> pd.DataFrame:
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError("NVE returned empty data.")

        return pd.DataFrame(data)

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Connection to NVE timed out."
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Could not retrieve data from NVE: {e}"
        )

    except ValueError as e:
        raise RuntimeError(
            f"Invalid response from NVE: {e}"
        )


def process_water_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renser og klargjør NVE-data.
    """

    df = df[
        df["neste_Publiseringsdato"] != "0001-01-01T00:00:00"
    ].copy()

    # Konverter datoer
    df["dato_Id"] = pd.to_datetime(df["dato_Id"])

    # Standardiser områdeverdier
    df["omrnr_std"] = df["omrnr"].astype(str)

    return df


def aggregate_water_data(
    df: pd.DataFrame,
    start_date,
    end_date,
    agg_func: str = "mean",
    value_col: str = "fyllingsgrad",
) -> pd.DataFrame:
    """
    Aggregerer fyllingsgrad for valgt periode per område.

    Parameters
    ----------
    df : prosessert DataFrame fra process_water_data
    start_date, end_date : periode å aggregere over (datetime-lignende)
    agg_func : 'mean', 'min', 'max', 'last'
    value_col : hvilken kolonne som skal aggregeres
    """
    mask = (df["dato_Id"] >= pd.to_datetime(start_date)) & (
        df["dato_Id"] <= pd.to_datetime(end_date)
    )
    filtered = df.loc[mask]

    if filtered.empty:
        return pd.DataFrame(columns=["omrnr_std", value_col])

    agg_df = (
        filtered.groupby("omrnr_std")[value_col]
        .agg(agg_func)
        .reset_index()
    )
    return agg_df


def get_water_values(
    gdf: gpd.GeoDataFrame,
    start_date,
    end_date,
    agg_func: str = "mean",
    value_col: str = "fyllingsgrad",
    id_col_geo: str = "budomr",
) -> gpd.GeoDataFrame:
    """
    Henter, renser, aggregerer og kobler NVE-magasindata
    til geometri (Budområder).
    """
    raw_df = get_water_data()
    clean_df = process_water_data(raw_df)
    agg_df = aggregate_water_data(
        clean_df, start_date, end_date, agg_func, value_col
    )

    merged = gdf.merge(
        agg_df, left_on=id_col_geo, right_on="omrnr_std", how="left"
    )

    return merged