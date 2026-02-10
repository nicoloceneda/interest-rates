# Term Structure of Interest Rates

![Project cover](assets/project_cover.png)

![Status: Active Development and Maintained](https://img.shields.io/badge/status-active%20development%20%26%20maintained-brightgreen)

*Author*: Nicolo Ceneda \
*Contact*: n.ceneda20@imperial.ac.uk \
*Website*: [nicoloceneda.github.io](https://nicoloceneda.github.io/) \
*Institution*: Imperial College London \
*Course*: PhD in Finance

## Description

This project downloads and analyzes the U.S. Treasury zero-coupon yield curve. It includes:
- `data.py` to download and clean the full historical yield curve dataset (Gurkaynak-Sack-Wright data from the Federal Reserve).
- `app.py` to run an interactive Streamlit dashboard.

## Installation

Create and activate a virtual environment:

```bash
conda create -n envIR python=3.12 -y
conda activate envIR
```

Install dependencies from `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Download and prepare the yield data:

```bash
python data.py
```

Run the dashboard:

```bash
streamlit run app.py
```
