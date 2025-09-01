import altair as alt
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

st.set_page_config(
    page_title="CPI • USD vs Bitcoin",
    page_icon="₿",
    layout="centered",
)

st.title("The Consumer Price Index Through Two Lenses: Dollars vs. Bitcoin")
st.caption(
    "Explore how inflation in USD compares to deflationary Bitcoin (expressed in sats).")


@st.cache_data
def load_series():
    df = pd.read_csv("ap.series", sep="\t", dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())

    # drop duplicate id/title combos
    df = df.drop_duplicates(subset=["series_id", "series_title"])

    # keep only titles containing "U.S. City Average"
    df = df[df["series_title"].str.contains(
        "U.S. City Average", case=False, na=False)]

    # sort alphabetically
    df = df.sort_values(by="series_title", ascending=True)

    # filter by end year
    df["end_year"] = pd.to_numeric(df["end_year"], errors="coerce")
    df = df[df["end_year"] >= 2017]

    return df[["series_id", "series_title"]].to_dict(orient="records")


@st.cache_data
def load_price():
    df = pd.read_csv("ap.data.0.Current", sep="\t",
                     dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"] >= 2017]
    return df[["series_id", "year", "period", "value"]]


@st.cache_data
def load_bitcoin_price():
    df = pd.read_csv("bitcoin.price.period", sep="\t",
                     dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"] >= 2017]
    return df[["year", "period", "value"]]


series = load_series()
prices = load_price()
bitcoin_prices = load_bitcoin_price()

options = [None] + series

selected = st.selectbox(
    "Select CPI Series Item to view price info",
    options,
    format_func=lambda r: r["series_title"] if isinstance(
        r, dict) else "-- Select a series --",
    index=0
)

if not selected:
    st.info("Please select a series to continue.")
else:
    series_id = selected["series_id"]
    series_title = selected["series_title"]
    st.write(f"**Selected CPI Series ID:** `{series_id}`")
    st.write(f"`{series_title}`")

    # Filter prices for this series and year
    df_filtered = prices[(prices["series_id"] == series_id)]

   # Ensure numeric value
    df_filtered = df_filtered.copy()
    df_filtered["value"] = pd.to_numeric(df_filtered["value"], errors="coerce")

    # Filter year
    df_filtered = df_filtered.copy()
    df_filtered["year"] = df_filtered["year"].astype(int)
    # df_filtered = df_filtered[df_filtered["year"] >= 2017]

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

    # --- bring in bitcoin price ---
    bitcoin_prices = bitcoin_prices.copy()
    bitcoin_prices["year"] = bitcoin_prices["year"].astype(int)
    # Clean the value text: remove $ signs, commas, NBSPs, and any odd unicode separators
    bitcoin_prices["value"] = (
        bitcoin_prices["value"]
        .astype(str)
        .str.replace(r"[\$\s,]", "", regex=True)          # $, spaces, commas
        .str.replace("\u00A0", "", regex=False)           # non-breaking space
        # narrow no-break space
        .str.replace("\u202F", "", regex=False)
        # anything not 0-9 . -
        .str.replace(r"[^\d\.\-]", "", regex=True)
    )

    bitcoin_prices["value"] = pd.to_numeric(
        bitcoin_prices["value"], errors="coerce")

    # some datasets may have multiple periods per year, so take the mean
    btc_annual = bitcoin_prices.groupby(
        "year", as_index=False).agg(bitcoin_price=("value", "mean"))

    # merge with CPI annual averages
    merged = pd.merge(annual_table, btc_annual, on="year", how="left")

    # compute price in BTC terms
    merged["price_in_usd"] = merged["avg_price"]
    merged["price_in_bitcoin"] = merged["avg_price"] / merged["bitcoin_price"]
    merged["price_in_sats"] = merged["price_in_bitcoin"] * 100_000_000
    merged["price_in_sats"] = merged["price_in_sats"].round(2)
    merged["bitcoin_price"] = merged["bitcoin_price"].round(2)

    # display
    st.write("##### Annual average price (USD and Bitcoin)")

    df_display = merged.copy()
    df_display["Price (USD)"] = df_display["price_in_usd"].map(
        lambda x: f"$ {x:,.2f}")
    df_display["Price (Bitcoin)"] = df_display["price_in_bitcoin"].map(
        lambda x: f"{x:,.8f} \u20BF")
    df_display["Price (Sats)"] = df_display["price_in_sats"].map(
        lambda x: f"{x:,.2f} sats")
    df_display["BTC/USD Avg"] = df_display["bitcoin_price"].map(
        lambda x: f"$ {x:,.2f}")

    st.dataframe(
        df_display[["year", "Price (USD)", "Price (Bitcoin)",
                    "Price (Sats)", "BTC/USD Avg", "months", "source"]]
        .rename(columns={"year": "Year", "months": "Months Used", "source": "Method"}),
        use_container_width=True
    )

    # Nice legend labels by renaming first
    plot_df = merged.rename(columns={
        "price_in_usd": "Price (USD)",
        "price_in_bitcoin": "Price (Bitcoin)",
        "price_in_sats": "Price (Sats)",
    })

    # Ensure year is numeric for plotting
    plot_df = plot_df.copy()
    plot_df["year"] = plot_df["year"].astype(int)

    # Charts
    base = alt.Chart(plot_df).encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0))
    )

    usd_chart = (
        base.mark_line(point=True)
        .encode(y=alt.Y("Price (USD):Q", title="Price (USD)"))
        .properties(width=700, height=260, title=f"{series_title} — Annual Average (USD)")
    )

    sats_chart = (
        base.mark_line(point=True)
        .encode(y=alt.Y("Price (Sats):Q", title="Price (sats)"))
        .properties(width=700, height=260, title=f"{series_title} — Annual Average (sats)")
    )

    st.altair_chart(alt.vconcat(usd_chart, sats_chart),
                    use_container_width=False)

st.markdown("---")
st.markdown(
    "Built by [lone-starr](https://github.com/lone-starr) • View source on [GitHub](https://github.com/lone-starr/price_dashboard)")
