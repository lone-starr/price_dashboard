import altair as alt
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

st.title("CPI Price Data")


@st.cache_data
def load_series():
    df = pd.read_csv("ap.series", sep="\t", dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())
    return df[["series_id", "series_title"]].to_dict(orient="records")


@st.cache_data
def load_price():
    df = pd.read_csv("ap.data.0.Current", sep="\t",
                     dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())
    return df[["series_id", "year", "period", "value"]]


series = load_series()
prices = load_price()

selectedYear = st.selectbox("Year", list(range(2009, datetime.now().year + 1)))

# Show titles in the dropdown, return the whole record
selected = st.selectbox(
    "Series Name",
    series,
    format_func=lambda r: r["series_title"] if isinstance(r, dict) else r,
)

if selected:
    series_id = selected["series_id"]
    series_title = selected["series_title"]
    st.write(f"**Selected ID:** `{series_id}`")
    st.caption(series_title)
    st.caption(f"Year: {selectedYear}")

    # Filter prices for this series and year
    df_filtered = prices[(prices["series_id"] == series_id)
                         & (prices["year"] == str(selectedYear))]

    if not df_filtered.empty:
        st.write("### Prices")
        st.dataframe(df_filtered)

        # Example: line chart of monthly values
        chart = alt.Chart(df_filtered).mark_line(point=True).encode(
            x="period:N",
            y="value:Q",
            tooltip=["period", "value"]
        ).properties(title=f"{series_title} ({selectedYear})")

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No data found for this year.")
