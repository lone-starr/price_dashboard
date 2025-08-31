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

    # Filter prices for this series and year
    df_filtered = prices[(prices["series_id"] == series_id)]

   # Ensure numeric value
    df_filtered = df_filtered.copy()
    df_filtered["value"] = pd.to_numeric(df_filtered["value"], errors="coerce")

    # Filter year
    df_filtered = df_filtered.copy()
    df_filtered["year"] = df_filtered["year"].astype(int)
    df_filtered = df_filtered[df_filtered["year"] >= 2009]

    # Annual (M13) rows
    annual_m13 = (
        df_filtered[df_filtered["period"] == "M13"][["year", "value"]]
        .rename(columns={"value": "avg_price"})
        .assign(source="BLS annual (M13)", months=12)
    )

    # Monthly rows M01–M12 -> average per year
    monthly = df_filtered[df_filtered["period"].str.match(
        r"^M(0[1-9]|1[0-2])$")].copy()
    monthly_avg = (
        monthly.groupby("year", as_index=False)
        .agg(avg_price=("value", "mean"), months=("value", "count"))
        .assign(source=lambda d: d["months"].astype(str) + " mo avg")
    )

    # Prefer M13 when available; otherwise use monthly average
    m13_idx = annual_m13.set_index("year")
    mon_idx = monthly_avg.set_index("year")
    annual_table = m13_idx.combine_first(mon_idx).reset_index()

    # Nice sorting & types
    annual_table["year"] = annual_table["year"].astype(int)
    annual_table = annual_table.sort_values("year")

    st.write("### Annual average price by year")
    st.dataframe(
        annual_table.rename(columns={
            "year": "Year",
            "avg_price": "Average Price",
            "months": "Months Used",
            "source": "Method"
        }),
        use_container_width=True
    )

    # (Optional) annual chart instead of monthly
    chart = (
        alt.Chart(annual_table)
        .mark_line(point=True)
        .encode(
            x=alt.X("year:O", title="Year", sort=None),
            y=alt.Y("avg_price:Q", title="Average Price"),
            tooltip=["year", "avg_price", "source", "months"]
        )
        .properties(title=f"{series_title} — Annual Average")
    )
    st.altair_chart(chart, use_container_width=True)
