import time
import numpy as np
import pandas as pd
from river import time_series, linear_model, optim, preprocessing, metrics
import requests


def backtest_snarimax(
    nve_monthly: pd.DataFrame,
    exogenous_data: pd.DataFrame | None = None,
    target_col: str = "fyllingsgrad",
    exogenous_cols: list[str] | None = None,
    history_months: int = 36,
    horizon_months: int = 3,
    param_grid: list[dict] | None = None,
    n_folds: int = 5,
) -> pd.DataFrame:
    """
    Walk-forward backtesting av SNARIMAX for ulike parametersett.

    For hvert fold trenes modellen på `history_months` måneder som ender
    ved et "cutoff"-tidspunkt, og prognosen for de neste `horizon_months`
    måneder sammenlignes med faktiske observerte verdier (MAE/RMSE).
    Cutoff flyttes fremover for hvert fold (n_folds stk, jevnt fordelt).

    NB: I backtesten brukes de *faktiske* fremtidige eksogene verdiene
    (perfekt informasjon) for å isolere modellens egen prediksjonsevne —
    dette er optimistisk sammenlignet med reell drift, hvor fremtidige
    eksogene verdier er ukjente.

    Returns
    -------
    pd.DataFrame med én rad per (parametersett, fold): MAE, RMSE, kjøretid.
    """
    exogenous_cols = exogenous_cols or []

    merged = nve_monthly[[target_col]].copy()
    if exogenous_cols:
        merged = merged.join(exogenous_data[exogenous_cols], how="inner")
    merged = merged.sort_index().dropna()

    if param_grid is None:
        param_grid = [
            dict(p=1, d=0, q=0, m=12, sp=0, sd=0, sq=0),
            dict(p=1, d=0, q=1, m=12, sp=1, sd=0, sq=0),
            dict(p=2, d=0, q=1, m=12, sp=1, sd=0, sq=0),
            dict(p=2, d=1, q=1, m=12, sp=1, sd=0, sq=1),
        ]

    min_start = history_months
    max_start = len(merged) - horizon_months
    if max_start <= min_start:
        raise ValueError("Ikke nok data til valgt history_months + horizon_months.")

    cutoffs = np.linspace(min_start, max_start, n_folds, dtype=int)
    results = []

    for params in param_grid:
        for cutoff in cutoffs:
            train = merged.iloc[cutoff - history_months: cutoff]
            test = merged.iloc[cutoff: cutoff + horizon_months]
            if len(test) < horizon_months:
                continue

            t0 = time.time()
            regressor = (
                preprocessing.StandardScaler()
                | linear_model.LinearRegression(optimizer=optim.SGD(0.01))
            )
            model = time_series.SNARIMAX(regressor=regressor, **params)

            for _, row in train.iterrows():
                y = row[target_col]
                x = row[exogenous_cols].to_dict() if exogenous_cols else None
                model.learn_one(y=y, x=x)

            xs = test[exogenous_cols].to_dict("records") if exogenous_cols else None
            preds = model.forecast(horizon=horizon_months, xs=xs)
            runtime = time.time() - t0

            mae, rmse = metrics.MAE(), metrics.RMSE()
            for y_true, y_pred in zip(test[target_col], preds):
                mae.update(y_true, y_pred)
                rmse.update(y_true, y_pred)

            results.append({
                **params,
                "history_months": history_months,
                "horizon_months": horizon_months,
                "cutoff_date": merged.index[cutoff],
                "mae": mae.get(),
                "rmse": rmse.get(),
                "runtime_sec": runtime,
            })

    return pd.DataFrame(results)


from river import time_series, preprocessing, linear_model, optim
import pandas as pd


def forecast_reservoir_filling(
    monthly_data,
    target_col="fyllingsgrad",
    history_months=12,
    horizon_months=6,
    p=1,
    d=1,
    q=0,
    m=12,
    sp=0,
    sd=0,
    sq=0,
):
    """
    Forecast reservoir filling for one NVE region.

    Uses a River SNARIMAX model trained on monthly observations.
    """

    # Select target and remove missing observations
    data = monthly_data[[target_col]].copy()
    data = data.sort_index().dropna()

    # Use only the most recent observations
    train_data = data.tail(history_months)

    if len(train_data) < history_months:
        raise ValueError(
            "Not enough historical observations for the selected history length."
        )

    # Create the SNARIMAX model
    model = time_series.SNARIMAX(
        p=p,
        d=d,
        q=q,
        m=m,
        sp=sp,
        sd=sd,
        sq=sq,
        regressor=(
            preprocessing.StandardScaler()
            | linear_model.LinearRegression(
                optimizer=optim.SGD(0.01)
            )
        ),
    )

    # Train the model one observation at a time
    for value in train_data[target_col]:
        model.learn_one(y=float(value))

    # Generate forecasts
    predictions = model.forecast(horizon=horizon_months)

    # Create monthly dates for the forecast
    last_date = train_data.index[-1]

    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=horizon_months,
        freq="MS",
    )

    forecast = pd.Series(
        predictions,
        index=forecast_dates,
        name="forecast",
    )

    return forecast, model, train_data

def download_nve_data():

    # Define the NVE API URL for reservoir statistics
    url = (
        "https://biapi.nve.no/magasinstatistikk/"
        "api/Magasinstatistikk/HentOffentligData"
    )

    # Send a GET request to the API
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Convert the JSON response into a pandas DataFrame
    data = response.json()
    nve_df = pd.DataFrame(data)

    # Remove invalid publication dates
    nve_df = nve_df[
        nve_df["neste_Publiseringsdato"] != "0001-01-01T00:00:00"
    ].copy()

    # Convert the date column to datetime format
    nve_df["dato_Id"] = pd.to_datetime(nve_df["dato_Id"])

    # Return the cleaned reservoir data
    return nve_df

def prepare_nve_data(nve_df, area_number=1):

    # Select reservoir data for the specified electricity price area
    region_data = nve_df[
        (nve_df["omrType"] == "EL") &
        (nve_df["omrnr"] == area_number)
    ].copy()

    # Aggregate reservoir data into monthly averages
    monthly = (
        region_data
        .set_index("dato_Id")
        [["fyllingsgrad", "fylling_TWh", "kapasitet_TWh"]]
        .resample("MS")
        .mean()
        .dropna()
    )

    # Remove potentially incomplete first and last months
    monthly = monthly.iloc[1:-1].copy()

    # Return the prepared monthly dataset
    return monthly

def get_nve_monthly_data(area_number=1):

    # Download raw NVE data
    nve_df = download_nve_data()

    # Prepare monthly data for the selected area
    nve_monthly = prepare_nve_data(
        nve_df,
        area_number=area_number
    )

    return nve_monthly