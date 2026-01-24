# %% SETUP

# Import the libraries

import requests
import pandas as pd
from pathlib import Path


# %% YIELDS

# Function to download data from url

def download_data(url, file_path):
    
    try:
        # Download file
        response = requests.get(url)
        response.raise_for_status()

        # Write content to temporary zip file
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f'File downloaded and saved to {file_path}')

    except requests.exceptions.RequestException as e:
        print(f'Error downloading data: {e}')

# Download the data

dir_raw = Path('data/gurkaynak/raw')
dir_raw.mkdir(parents=True, exist_ok=True)

url = f'https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv'
file_path = dir_raw / 'yields.csv'
download_data(url, file_path)

# Import the zero coupon bond yields

df_yields = pd.read_csv(file_path, skiprows=9, index_col='Date', parse_dates=True)
columns = [col for col in df_yields.columns if col.startswith('SVENY')]
df_yields = df_yields[columns]

# Clean the data

df_yields.rename(columns={col: str(int(col[5:])) + 'y' for col in columns}, inplace=True)
df_yields = df_yields['1985-11-25':]
df_yields = df_yields.dropna()

# Save the data

dir_ext = Path('data/gurkaynak/extracted')
dir_ext.mkdir(parents=True, exist_ok=True)
df_yields.to_csv(dir_ext / 'yields.csv')
