
import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

from Mangodb import get_data, get_filter_options


st.title("Cross-border electricity flows")
st.write(
    "Explore electricity transfers to and from Norway "
    "by connection, year and month."
)

try:
    connections, years = get_filter_options()

    if not connections or not years:
        st.warning("No connections or years were found in MongoDB.")
        st.stop()

    # Split the page into two columns
    left, right = st.columns(2)

    with left:
        st.subheader("Flow by direction")

        selected_connection = st.radio(
            "Select connection",
            options=connections,
            key="selected_connection"
        )

        selected_year = st.selectbox(
            "Select year",
            options=years,
            key="selected_year"
        )

    # Fetch only the selected connection and year
    df = get_data(selected_connection, selected_year)

    if df.empty:
        st.warning("No data found for this connection and year.")
        st.stop()

    with left:
        # Sum the flow for each direction
        pie_data = (
            df.groupby("direction", as_index=False)["flow_mw"]
            .sum()
        )

        if not pie_data.empty:
            pie_fig = px.pie(
                pie_data,
                names="direction",
                values="flow_mw",
                title=f"Total flow by direction in {selected_year}",
                hole=0.25
            )
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No data available for the pie chart.")

    with right:
        st.subheader("Flow over selected months")

        month_options = list(range(1, 13))

        selected_months = st.pills(
            "Select months",
            options=month_options,
            default=[1, 2, 3],
            selection_mode="multi",
            format_func=lambda month: calendar.month_abbr[month],
            key="selected_months"
        )

        if selected_months:
            month_df = df[df["month"].isin(selected_months)].copy()
            month_df = month_df.sort_values("timestamp")

            if not month_df.empty:
                line_fig = px.line(
                    month_df,
                    x="timestamp",
                    y="flow_mw",
                    color="direction",
                    title="Electricity flow over time",
                    labels={
                        "timestamp": "Date",
                        "flow_mw": "Flow (MW)",
                        "direction": "Direction"
                    }
                )

                line_fig.update_layout(
                    legend_title_text="Direction",
                    hovermode="x unified"
                )

                st.plotly_chart(
                    line_fig,
                    use_container_width=True
                )
            else:
                st.info("No data exists for the selected months.")
        else:
            st.info("Select at least one month to display the line plot.")

except Exception as error:
    st.error(f"Could not load MongoDB data: {error}")


# Document the data source
with st.expander("About the data source"):
    st.markdown(
        """
        The data on this page comes from the MongoDB Atlas database
        `energy`, collection `cross_border_flows_spark`.

        The collection contains cross-border electricity flow data
        retrieved from the ENTSO-E data source and stored in MongoDB.

        - **Connection:** the selected cross-border connection.
        - **Year:** the selected year of observations.
        - **Direction:** the recorded direction of electricity flow.
        - **Flow (MW):** the recorded electricity flow in megawatts.
        - **Months:** the months included in the time-series chart.

        The pie chart sums the recorded flow by direction for the
        selected connection and year. The line chart displays the
        recorded observations for the selected months.
        """
    )
