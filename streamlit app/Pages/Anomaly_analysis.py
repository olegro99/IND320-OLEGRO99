
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import LocalOutlierFactor

st.title("Anomaly and Outlier Detection")

st.write(
    "Explore unusual observations in the weather data "
    "using Statistical Process Control (SPC) and "
    "Local Outlier Factor (LOF)."
)



# Load weather data from session state


if "weather_daily" not in st.session_state:
    st.warning(
        "No weather data found. Go to the Meteorological Data "
        "page and download weather data first."
    )
    st.stop()

# Load daily weather data
weather_data = st.session_state["weather_daily"].copy()

if weather_data.empty:
    st.warning("The weather dataset is empty.")
    st.stop()

# Convert date column to datetime
weather_data["date"] = pd.to_datetime(
    weather_data["date"],
    errors="coerce"
)

weather_data = weather_data.dropna(subset=["date"])


# Select variable for analysis


st.subheader("Data selection")

# Find numerical weather variables
numeric_columns = weather_data.select_dtypes(
    include="number"
).columns.tolist()

if not numeric_columns:
    st.error("No numerical variables found.")
    st.stop()

# Select a default variable
default_variable = (
    "temperature_2m"
    if "temperature_2m" in numeric_columns
    else numeric_columns[0]
)

selected_variable = st.selectbox(
    "Select variable",
    numeric_columns,
    index=numeric_columns.index(default_variable)
)

# Prepare the selected time series
time_series = weather_data[
    ["date", selected_variable]
].copy()

time_series = time_series.dropna()
time_series = time_series.sort_values("date")

# Group observations by date
time_series = (
    time_series.groupby("date")[selected_variable]
    .mean()
)

if len(time_series) < 5:
    st.warning(
        "There are too few observations for anomaly detection. "
        "Download a longer period of weather data."
    )
    st.stop()

# Display the original data
st.write(f"Selected variable: **{selected_variable}**")
st.write(f"Number of observations: **{len(time_series)}**")

st.subheader("Original time series")
st.line_chart(time_series)


# --------------------------------------------------
# Create tabs
# --------------------------------------------------

spc_tab, lof_tab = st.tabs(
    ["Outlier detection / SPC", "Anomaly detection / LOF"]
)


# OUTLIER DETECTION / SPC

with spc_tab:

    st.header("Statistical Process Control (SPC)")

    st.write(
        "A control chart is used to identify observations "
        "that fall outside the expected variation of a time series."
    )

    st.write(
        "The control limits are calculated using the mean "
        "and standard deviation of the selected variable."
    )

    # Select the number of standard deviations
    sigma = st.slider(
        "Control limit (standard deviations)",
        min_value=1.0,
        max_value=4.0,
        value=3.0,
        step=0.5
    )

    if st.button("Run SPC analysis"):

        # Calculate the center line and control limits
        mean_value = time_series.mean()
        std_value = time_series.std()

        upper_limit = mean_value + sigma * std_value
        lower_limit = mean_value - sigma * std_value

        # Identify observations outside the control limits
        outliers = (
            (time_series > upper_limit)
            | (time_series < lower_limit)
        )

        # Create a DataFrame with the results
        spc_results = pd.DataFrame({
            "Value": time_series,
            "Upper control limit": upper_limit,
            "Center line": mean_value,
            "Lower control limit": lower_limit,
            "Outlier": outliers
        })

        # Display summary statistics
        st.subheader("SPC results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mean", f"{mean_value:.2f}")

        with col2:
            st.metric("Standard deviation", f"{std_value:.2f}")

        with col3:
            st.metric("Number of outliers", int(outliers.sum()))

        # Create control chart
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            time_series.index,
            time_series.values,
            label="Observed values",
            marker="o"
        )

        ax.axhline(
            mean_value,
            linestyle="--",
            label="Center line"
        )

        ax.axhline(
            upper_limit,
            linestyle="--",
            label="Upper control limit"
        )

        ax.axhline(
            lower_limit,
            linestyle="--",
            label="Lower control limit"
        )

        # Highlight outliers
        ax.scatter(
            time_series.index[outliers],
            time_series[outliers],
            label="Outliers",
            marker="x",
            s=80
        )

        ax.set_title("SPC Control Chart")
        ax.set_xlabel("Date")
        ax.set_ylabel(selected_variable)
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        # Display detected outliers
        st.subheader("Detected outliers")

        if outliers.any():
            st.dataframe(
                spc_results[outliers],
                use_container_width=True
            )
        else:
            st.success("No observations outside the control limits.")

        # Display all results
        with st.expander("Show all SPC results"):
            st.dataframe(
                spc_results,
                use_container_width=True
            )


# ANOMALY DETECTION / LOF

with lof_tab:

    st.header("Local Outlier Factor (LOF)")

    st.write(
        "Local Outlier Factor identifies observations that "
        "have a substantially lower local density than their "
        "neighbours. These observations may be considered anomalies."
    )

    st.write(
        "In this analysis, LOF is applied to the selected "
        "weather variable."
    )

    # Choose the number of neighbours
    max_neighbors = min(50, len(time_series) - 1)
    default_neighbors = min(20, max_neighbors)

    n_neighbors = st.slider(
        "Number of neighbours",
        min_value=2,
        max_value=max_neighbors,
        value=default_neighbors
    )

    # Choose the expected proportion of anomalies
    contamination = st.slider(
        "Expected proportion of anomalies",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
        format="%.2f"
    )

    if st.button("Run LOF analysis"):

        # Convert the time series to a two-dimensional array
        values = time_series.values.reshape(-1, 1)

        # Create and fit the LOF model
        lof_model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination
        )

        # Predict normal observations (1) and anomalies (-1)
        predictions = lof_model.fit_predict(values)

        # Create a results DataFrame
        lof_results = pd.DataFrame({
            "Value": time_series.values,
            "LOF prediction": predictions,
            "Anomaly": predictions == -1,
            "LOF score": -lof_model.negative_outlier_factor_
        }, index=time_series.index)

        # Count detected anomalies
        anomalies = lof_results["Anomaly"]

        st.subheader("LOF results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Observations",
                len(lof_results)
            )

        with col2:
            st.metric(
                "Detected anomalies",
                int(anomalies.sum())
            )

        with col3:
            st.metric(
                "Anomaly percentage",
                f"{anomalies.mean() * 100:.1f}%"
            )

        # Plot the time series and highlight anomalies
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            time_series.index,
            time_series.values,
            label="Observed values",
            marker="o"
        )

        ax.scatter(
            lof_results.index[anomalies],
            lof_results.loc[anomalies, "Value"],
            label="Detected anomalies",
            marker="x",
            s=100
        )

        ax.set_title("LOF Anomaly Detection")
        ax.set_xlabel("Date")
        ax.set_ylabel(selected_variable)
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        # Display detected anomalies
        st.subheader("Detected anomalies")

        if anomalies.any():
            st.dataframe(
                lof_results[anomalies],
                use_container_width=True
            )
        else:
            st.success("No anomalies detected.")

        # Display all results
        with st.expander("Show all LOF results"):
            st.dataframe(
                lof_results,
                use_container_width=True
            )
