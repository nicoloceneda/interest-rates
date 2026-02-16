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
- `app.py` to launch an interactive Streamlit dashboard.
- `src/` as a modular dashboard package with:
  - `src/data/` loaders and FRED API connectors.
  - `src/transforms/` spread/factor/regime analytics.
  - `src/charts/` reusable Altair chart builders.
  - `src/tabs/` tab-level dashboard renderers.

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

## Set FRED API Key (for Macro Context tab)

If you do not set the key, the dashboard still runs, but FRED-powered macro overlays are disabled.

### Option A (recommended): Streamlit secrets file

1. In the project root, create the secrets folder:

```bash
mkdir -p .streamlit
```

2. Create `.streamlit/secrets.toml` with this exact content:

```toml
FRED_API_KEY = "your_api_key_here"
```

3. Start the dashboard:

```bash
streamlit run app.py
```

4. Check the sidebar:
- If configured correctly, you should see `FRED key detected`.
- If not, you will see `FRED key missing`.

### Option B: environment variable

Set it for the current terminal session:

```bash
export FRED_API_KEY="your_api_key_here"
streamlit run app.py
```

To persist it on macOS `zsh`, add it to your shell config:

```bash
echo 'export FRED_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Security notes

- Never commit your key to git.
- `.gitignore` already excludes `.streamlit/` and `.env*`.
- If a key is ever exposed, rotate/regenerate it from your FRED account.

### Troubleshooting

- If you still see `FRED key missing`, fully stop and restart Streamlit.
- If using env vars, verify the key is set in the same shell where you run Streamlit:

```bash
echo "$FRED_API_KEY"
```

- If using secrets file, verify the path is exactly `.streamlit/secrets.toml` (in project root).

Run the dashboard:

```bash
streamlit run app.py
```

## Dashboard Tabs

- `Curve`: snapshot and date-over-date curve comparison.
- `Historical`: multi-maturity yield history with date-range filtering.
- `Spreads`: key spread monitoring plus custom spread builder.
- `Factors`: level, slope, curvature decomposition.
- `Heatmap`: yield levels and daily change heatmaps.
- `Volatility`: rolling realized volatility by maturity.
- `Regimes`: regime timeline and distribution diagnostics.
- `Macro Context`: FRED overlays with recession shading.

## Testing

Run unit tests:

```bash
pytest
```
