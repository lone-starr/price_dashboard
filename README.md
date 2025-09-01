# Price Charts

This repository builds a basic dashboard using CPI data from https://download.bls.gov/pub/time.series/ap/ and Bitcoin price data from https://www.in2013dollars.com/bitcoin-price

View charts at https://cpi.lonestarr.xyz/

## Setting Up

Clone the Repository:

```bash
git clone https://github.com/lone-starr/price_dashboard.git
```

```bash
cd price_dashboard
```

## Create a fresh Python virtual environment

```bash
python3 -m venv .
```

## Select Python interpretor (Visual Studio Code)

Open VS Code from the price_dashboard directory:

```bash
code .
```

In VS Code press < Ctrl >< Shift >< p >, type Python and choose 'Python: Select Interpretor', choose the newly created venv for price_dashboard

## Install Dependencies

Open a new Terminal in VS Code and use the following command to install the required dependencies. Your Python venv should be indicated in your terminal shell.

```bash
pip install -r requirements.txt
```

## Run locally

Run the Streamlit App:

```bash
streamlit run app.py
```
