
import os

import pandas as pd
import pymongo
import streamlit as st


@st.cache_resource
def init_connection():
    mongo_uri = st.secrets["MONGO_URI"]

    client = pymongo.MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")
    return client


client = init_connection()
collection = client["energy"]["cross_border_flows_spark"]


@st.cache_data(ttl=600)
def get_filter_options():
    """Get available connections and years from MongoDB."""
    connections = collection.distinct("connection")
    raw_years = collection.distinct("year")

    connections = sorted(
        [str(value) for value in connections if value is not None]
    )

    years = sorted(
        {int(value) for value in raw_years if value is not None},
        reverse=True
    )

    return connections, years


@st.cache_data(ttl=600)
def get_data(connection, year):
    """Retrieve data for one connection and year."""
    query = {
        "connection": connection,
        "year": {"$in": [year, str(year)]}
    }

    projection = {
        "_id": 0,
        "connection": 1,
        "direction": 1,
        "year": 1,
        "timestamp": 1,
        "flow_mw": 1
    }

    items = list(collection.find(query, projection))
    df = pd.DataFrame(items)

    if not df.empty:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
            utc=True
        )
        df["flow_mw"] = pd.to_numeric(
            df["flow_mw"],
            errors="coerce"
        )
        df["direction"] = df["direction"].fillna("Unknown")

        df = df.dropna(subset=["timestamp", "flow_mw"])
        df["month"] = df["timestamp"].dt.month

    return df
