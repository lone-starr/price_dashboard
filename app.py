import altair as alt
import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv(".env")

st.title("CPI Price Data")


@st.cache_data
def load_series():
    df = pd.read_csv("ap.series", sep="\t", dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip())
    return df[["series_id", "series_title"]].to_dict(orient="records")


records = load_series()

# Show titles in the dropdown, return the whole record
selected = st.selectbox(
    "Series Name",
    records,
    format_func=lambda r: r["series_title"] if isinstance(r, dict) else r,
)

if selected:
    series_id = selected["series_id"]
    series_title = selected["series_title"]
    st.write(f"**Selected ID:** `{series_id}`")
    st.caption(series_title)
