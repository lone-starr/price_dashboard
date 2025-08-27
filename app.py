import altair as alt
import os
import streamlit as st
from pymongo import MongoClient
from pandas import DataFrame
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv(".env")

MONGO_URI = os.environ.get('MONGO_URI')

st.title("Bitcoin Mempool Dashboard")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['mempool']
collection = db['blockheight']

result = collection.find_one(sort=[('ts', -1)])
st.write(f"Current Block: {result.get('height')}")
st.write(f"Bitcoin Price: ${format(result.get('priceUSD'), ',')}")
st.write(
    f"Network Hashrate: {format(int(result.get('hashrate')/1000), ',')}&nbsp;EH/s")
st.write(f"Fastest Fee: {result.get('fastestFee')}&nbsp;sat/vB")
st.write(f"Hour Fee: {result.get('hourFee')}&nbsp;sat/vB")
st.write(f"Min Fee: {result.get('minimumFee')}&nbsp;sat/vB")
st.write(f"Difficulty: {result.get('diff')}&nbsp;")

asOfDate = result.get('ts').strftime("%B %d, %Y %I:%M %p")
st.write(f"As of {asOfDate} UTC")

range = st.selectbox(
    'Pick the time period. Data frequency is approx. 5 minute polling intervals', ('24 hour', '3 day', '7 day', '14 day', '28 day', 'full history'))

# default to 24 hour time period
delta = timedelta(hours=24)
if range == '3 day':
    delta = timedelta(days=3)
elif range == '7 day':
    delta = timedelta(days=7)
elif range == '14 day':
    delta = timedelta(days=14)
elif range == '28 day':
    delta = timedelta(days=28)
elif range == 'full history':
    delta = timedelta(weeks=99)

# Fee chart
st.write("Fastest and Minimum fees over time")
result = collection.find({"ts": {"$gt": datetime.now() - delta}},   {
    "_id": 0,
    "time": {
        "$dateAdd": {
            "startDate": "$ts",
            "unit": "hour",
            "amount": -5
        }
    }, "min fee": "$minimumFee", "fast fee": "$fastestFee", "hour fee": "$hourFee"
})
st.line_chart(result, x="time", y=["min fee", "fast fee", "hour fee"])
# st.divider()
# Price chart
st.write("Bitcoin conversion rate in USD")
result = collection.find({"ts": {"$gte": datetime.now() - delta}},   {
    "_id": 0,
    "time": {
        "$dateAdd": {
            "startDate": "$ts",
            "unit": "hour",
            "amount": -5
        }
    }, "USD": "$priceUSD"
})
# st.line_chart(result, x="time", y=["USD"])
resultDF = DataFrame(result)
altair_chart = alt.Chart(resultDF).mark_line(
    interpolate='step-after').encode(x=alt.X('time'), y=alt.Y('USD', scale=alt.Scale(domain=[90000, 120000])))

st.altair_chart(altair_chart, use_container_width=True)
# st.divider()
# Mempool / Hashrate chart
st.write("Mempool Transaction Count and Hash Rate over time")
result = collection.find({"ts": {"$gte": datetime.now() - delta}},   {
    "_id": 0,
    "time": {
        "$dateAdd": {
            "startDate": "$ts",
            "unit": "hour",
            "amount": -5
        }},
    "mempool size": {"$divide": ["$vsize", 1000]}, "tx count": "$count", "vsize": 1, "hashrate": 1
})
st.line_chart(result, x="time", y=["tx count", "mempool size", "hashrate"])

mongo_client.close()
