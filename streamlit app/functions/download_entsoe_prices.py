import pandas as pd
from entsoe import EntsoePandasClient

def download_entsoe_prices(start_date: str, end_date: str, api_key: str,
                            zones=("NO_1", "NO_2", "NO_3", "NO_4", "NO_5")):
    """
    Download ENTSO-E day-ahead prices for Norwegian bidding zones.

    Parameters
    ----------
    start_date, end_date : str (YYYY-MM-DD)
    api_key : str
    zones : iterable of ENTSO-E zone codes

    Returns
    -------
    pd.DataFrame with columns: timestamp, price_eur_mwh, zone
    """
    client = EntsoePandasClient(api_key=api_key)
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC")

    all_prices = []

    for zone in zones:
        try:
            series = client.query_day_ahead_prices(zone, start=start, end=end)
            df = series.rename("price_eur_mwh").rename_axis("timestamp").reset_index()
            df["zone"] = zone
            all_prices.append(df)
            print(f"OK: {zone}, {len(df)} rows")
        except Exception as e:
            print(f"FAILED: {zone}: {e}")

    if not all_prices:
        raise ValueError("No ENTSO-E price data was retrieved.")

    prices_df = pd.concat(all_prices, ignore_index=True)
    prices_df = prices_df.drop_duplicates(subset=["timestamp", "zone"])
    prices_df = prices_df.sort_values(["timestamp", "zone"]).reset_index(drop=True)

    return prices_df

def get_price_values_for_date(prices_df: pd.DataFrame, selected_date: str,
                               agg: str = "mean") -> dict:
    """
    Aggregate day-ahead prices for a single date, keyed by budomr format.

    Parameters
    ----------
    prices_df : output from download_entsoe_prices()
    selected_date : str (YYYY-MM-DD)
    agg : "mean" or "max"/"min" etc.

    Returns
    -------
    dict {"NO 1": value, "NO 2": value, ...}
    """
    day_df = prices_df[prices_df["timestamp"].dt.date == pd.to_datetime(selected_date).date()]

    if day_df.empty:
        return {}

    grouped = day_df.groupby("zone")["price_eur_mwh"].agg(agg)

    # NO_1 -> "NO 1" to match budomr column in Budområder.geojson
    return {zone.replace("_", " "): value for zone, value in grouped.items()}