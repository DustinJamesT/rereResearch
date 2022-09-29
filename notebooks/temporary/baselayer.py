# %%
# -- example on using 'messycharts' chart tool

# %% [markdown]
# # -- notebook details

# %%
# -- folder requirements 

"""
- main 
  |
  |-- /charts/        -- folder to store chart outputs 
  |-- /data/          -- folder to save data outputs 
  |
  |-- /scripts/notebook.ipynb -- script to collect data and build slides with messaychart tool 
  |
  |-- messycharts.py -- chart tool for building messari slides 

"""

# %%
# -- packages 

# -- Messari (only need for data collection)
# -- Pillow 
# -- Pandas 
# -- Plotly

# -- messycharts (file)


# %% [markdown]
# # -- import

# %%
import pandas as pd 

from datetime import date
import datetime

import time

import requests
import os

# %%
from importlib import reload

import messycharts 
reload(messycharts)

from messycharts import messychart

# %%
from messari.messari import Messari
from messari.coingecko import CoinGecko
from messari.defillama import DeFiLlama
from messari.nfts import NFTPriceFloor
from messari.tokenterminal import TokenTerminal

messari = Messari(os.getenv('MESSARI_API'))
coingecko = CoinGecko()
defillama = DeFiLlama()
floor = NFTPriceFloor()
tokenterminal = TokenTerminal(api_key=os.getenv('TOKEN_TERMINAL_API'))

# %% [markdown]
# # -- Report Set up

# %%
report_title = 'Layer-1'

filepath_chart = '/home/runner/Messari-Reports/charts/' + report_title.lower() + '/'
filepath_data =  '/home/runner/Messari-Reports/data/'   + report_title.lower() + '/'

today = date.today()
today_str = today.strftime("%Y-%m-%d")

date_ranges = [30,90,180,365, 999]

# %% [markdown]
# # -- get data: TVL

# %%
chains = ['Ethereum', 'Solana', "Avalanche", "Polygon", 'Arbitrum', 'Optimism', 'Fantom', 'Near', 'BSC']
chain_tvls = defillama.get_chain_tvl_timeseries(chains, start_date="2021-01-01", end_date=today_str)


# %%
cosmos_chains = ['cosmos', 'osmosis', 'cronos', 'evmos', 'thorchain', 'kava', 'juno', 'secret', 'canto']
cosmos_tvls = defillama.get_chain_tvl_timeseries(cosmos_chains, start_date="2021-01-01", end_date=today_str)


# %%
cosmos_tvls['Cosmos'] = cosmos_tvls.sum(axis=1)


# %%
chain_tvls = chain_tvls.join(cosmos_tvls['Cosmos'])

# %% [markdown]
# # -- Get Data: Market Cap

# %%
now = datetime.datetime.now()
timestamp = round(datetime.datetime.timestamp(now))

# %%
slug_fixes = {
  'avalanche': 'avalanche-2',
  'bsc': 'binancecoin',
  'polygon': 'matic-network',
  'juno': 'juno-network'
}

# %%
for i, chain in enumerate(chains): 
  try: 
    slug = slug_fixes[chain.lower()] if chain.lower() in slug_fixes.keys() else chain.lower() 

    chain_df = coingecko.get_coin_range(slug, _from = 1609459200, to = timestamp )
    time.sleep(5)

    if i == 0: 
      mcap_df = chain_df['market_caps'].to_frame()
      mcap_df.columns = [chain]

    else: 
      temp_df = chain_df['market_caps'].to_frame()
      temp_df.columns = [chain]
      mcap_df = mcap_df.join(temp_df)

  except: 
    None 

# %%
for i, chain in enumerate(cosmos_chains): 
  try: 
    slug = slug_fixes[chain.lower()] if chain.lower() in slug_fixes.keys() else chain.lower() 

    chain_df = coingecko.get_coin_range(slug, _from = 1609459200, to = timestamp )
    time.sleep(5)

    if i == 0: 
      cosmos_df = chain_df['market_caps'].to_frame()
      cosmos_df.columns = [chain]

    else: 
      temp_df = chain_df['market_caps'].to_frame()
      temp_df.columns = [chain]
      cosmos_df = cosmos_df.join(temp_df)

  except: 
    None 

# %%
cosmos_df['Cosmos'] = cosmos_df.sum(axis=1)
mcap_df = mcap_df.join(cosmos_df['Cosmos'])

# %%
mcap_df.index.rename('date')

# %%
mcap_df.reset_index()

# %% [markdown]
# # -- Get Data: Daily Active Addresses + Alt Data

# %%
start = date(2021, 1, 1)
delta = today - start
days_back = delta.days


# %%
# -- daily active addresses 
url_daa = f'https://api.gokustats.xyz/daily-active-addresses/?daysBack={days_back}&percentChange=false&baseCurrency=USD'

resp = requests.get(url_daa)
daa_raw = resp.json()

daa_df = pd.DataFrame(daa_raw)

daa_df['date'] = pd.to_datetime(daa_df['date'])
daa_df.set_index('date', inplace= True)

# %%
daa_df['cosmos'] = daa_df['cosmoshub'] + daa_df['osmosis']
daa_df = daa_df.drop(columns=['flow', 'osmosis', 'cosmoshub'])

# %%
# -- daily txns
url_txns = f'https://api.gokustats.xyz/daily-transactions/?daysBack={days_back}&percentChange=false&baseCurrency=USD'

resp = requests.get(url_txns)
txns_raw = resp.json()

txns_df = pd.DataFrame(txns_raw)

txns_df['date'] = pd.to_datetime(txns_df['date'])
txns_df.set_index('date', inplace= True)


# %%

txns_df['cosmos'] = txns_df['cosmoshub'] + txns_df['osmosis']
txns_df = txns_df.drop(columns=['flow', 'osmosis', 'cosmoshub'])

# %%
# -- twitter followers 
url_twit = f'https://api.gokustats.xyz/cumulative-twitter-followers/?daysBack={days_back}&percentChange=false&baseCurrency=USD'

resp = requests.get(url_twit)
twit_raw = resp.json()

twit_df = pd.DataFrame(twit_raw)

twit_df['date'] = pd.to_datetime(twit_df['date'])
twit_df.set_index('date', inplace= True)


# %%
twit_df.rename(columns={'cosmoshub':'cosmos'}, inplace=True)
twit_df = twit_df.drop(columns=['flow', 'osmosis'])

# %%
# -- stables - alt (get from defi llama)
llama_stables_url = 'https://stablecoins.llama.fi/stablecoins?includePrices=false'

resp = requests.get(llama_stables_url)
stables_raw = resp.json()['peggedAssets']

#llama_stables_df = pd.DataFrame(stables_raw)

# %%
stables = ['USDT', 'USDC', 'BUSD', 'DAI', 'FRAX', 'TUSD', 'LUSD', 'MIM', 'FEI', 'USDP', 'USDN', 'USDD', 'SUSD']

stable_config = {}

for stable_data in stables_raw: 
  if stable_data['symbol'] in stables: 
    stable_config[ stable_data['symbol'] ] = stable_data['id']


# %%
# -- get llama data 
llama_stables = []

for chain in chains: 
  llama_base_url = f'https://stablecoins.llama.fi/stablecoincharts/{chain}?stablecoin='

  for stable, id in stable_config.items():
    llama_url = llama_base_url + id 

    resp = requests.get(llama_url)
    stables_raw_ = resp.json()

    time.sleep(0.335)

    for chain_stable in stables_raw_:
      try:
        dt = datetime.datetime.fromtimestamp(int(chain_stable['date']))
        date_str = dt.strftime("%Y-%m-%d")

        llama_stables.append({
          'date': date_str,
          'chain': chain,
          'token': stable,
          'TotalStablesUSD': chain_stable['totalCirculatingUSD']['peggedUSD'],
          'BridgedUSD': chain_stable['totalBridgedToUSD']['peggedUSD'],
          'MintedUSD': chain_stable['totalMintedUSD']['peggedUSD']
        })
      except: 
        None

stables_df = pd.DataFrame(llama_stables)

# %% [markdown]
# # -- group data 

# %%
"""
Dataframes: 
  - chain_tvls (defi llama)
  - mcap_df    (coingecko / Messari)
  - daa_df     (gokustats)
  - txns_df    (gokustats)
  - twit_df    (gokustats)
  - stables_df (defi llama) # -- note already in correct format
"""


# %%
def melt_df(df, col_name):
  # -- reset index and rename 
  cols = ['date'] if 'date' not in df.columns else []
  cols.extend(list(df.columns))
  temp_df = df.reset_index()
  temp_df.columns = cols 

  # -- melt df 
  final_df = pd.melt(temp_df, id_vars=['date'], value_vars= cols.remove('date') )
  final_df.columns = ['date', 'chain', col_name]

  final_df['date'] = pd.to_datetime(final_df['date'], format='%Y-%m-%d')
  final_df['chain'] = final_df.apply(lambda x: x.chain.capitalize(), axis=1)

  return final_df

# %%
chain_df = melt_df(chain_tvls, 'tvl')

# %%
dfs = [
  {'df': mcap_df, 'column': 'mcap'}, 
  {'df': daa_df,  'column': 'active_addrs'}, 
  {'df': txns_df, 'column': 'txns'}, 
  {'df': twit_df, 'column': 'twitter'},
  {'df': stables_df.groupby(['date', 'chain'])['TotalStablesUSD'].sum().unstack(), 'column': 'stable_supply'}
]

for df_ in dfs: 
  # -- melt df 
  temp_df = melt_df(df_['df'], df_['column'])

  # -- merge dfs 
  chain_df = chain_df.merge(temp_df, how = 'outer', on=["date","chain"])
  

# %%
chain_df = chain_df.drop(chain_df[chain_df.date < '2021-01-01'].index)

# %%
chain_df.replace('Bsc', 'BSC', inplace=True)

# %% [markdown]
# # -- save data

# %%
# -- save output 
chain_df.to_csv(filepath_data + 'chain_data_' + today_str +'.csv', index=False)
stables_df.to_csv(filepath_data + 'chain_stables_' + today_str +'.csv', index=False)

# %% [markdown]
# # -- CHART: Plot Basics 

# %%
chart_infos = {
  'tvl':           {'types': ['line','area'], 'name': 'TVL'}, 
  'mcap':          {'types': ['line','area'], 'name': 'Market Cap'}, 
  'active_addrs':  {'types': ['line'],        'name': 'Active Addresses'}, 
  'txns':          {'types': ['line'],        'name': 'Chain Transactions'}, 
  'twitter':       {'types': ['line'],        'name': 'Twitter Followers'}, 
  'stable_supply': {'types': ['bar','area'],  'name': 'Stablecoin Supply'}
}

# %%
# -- TVL Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'tvl'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'TVL Changes Across Major Ecosystems'
  chart.subtitle = '7d moving average of chain TVL over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of chain TVL over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of chain TVL since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, DeFi Llama'
  chart.note = 'Cosmos ecosystem TVL is a combination of top app chains'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Chain TVL',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

  # -- area chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Chain TVL',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)





# %%
# -- TVL Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'tvl'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    mcap_eth_df = chain_df[chain_df.chain == 'Ethereum'].groupby(['date', 'chain'])['mcap'].sum().unstack().rolling(moving_avg).mean()
    mcap_eth_df.columns = ['ETH Market Cap']

    plot_df = plot_df.join(mcap_eth_df)

    date_range = 'all'

  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

    mcap_eth_df = chain_df[chain_df.chain == 'Ethereum'].groupby(['date', 'chain'])['mcap'].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]
    mcap_eth_df.columns = ['ETH Market Cap']

    plot_df = plot_df.join(mcap_eth_df)

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'TVL Changes Across Major Ecosystems'
  chart.subtitle = '7d moving average of chain TVL over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of chain TVL over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of chain TVL since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, DeFi Llama'
  chart.note = 'Cosmos ecosystem TVL is a combination of top app chains'

  # -- area chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-withPrice-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Chain TVL',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                      secondary_column = 'ETH Market Cap',     # -- define which column to be the secondary axis 
                      secondary_axis_title = 'Ethereum Market Cap', # -- define the secondary axis title 
                      secondary_data_type= 'dollar',   # -- defines the data type of the secondary axis
                      show_secondary = False,            # -- controls whether to show item in legend 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)




# %%
# -- TVL Charts (no Ethereum)
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')
plot_chains.remove('Ethereum')

plot_column = 'tvl'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'TVL Changes Across Emerging Ecosystems'
  chart.subtitle = '7d moving average of chain TVL over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of chain TVL over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of chain TVL since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, DeFi Llama'
  chart.note = 'Cosmos ecosystem TVL is a combination of top app chains'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-NoETH-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Chain TVL',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

  # -- area chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-NoETH-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Chain TVL',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)




# %%
# -- Market Cap Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'mcap'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'Market Cap Changes Across Major Ecosystems'
  chart.subtitle = '7d moving average of base layer token market cap over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of base layer token market cap over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of base layer token market cap since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, CoinGecko'
  chart.note = 'Cosmos ecosystem market cap is a combination of top app chains'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Chain Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

  # -- area chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

# %%
# -- Active Addresses Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'active_addrs'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'Active Address Changes Across Major Ecosystems'
  chart.subtitle = '7d moving average of active addresses over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of active addresses over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of active addresses since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, GokuStats'
  chart.note = 'Cosmos active addresses is combination of CosmosHub and Osmosis'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Active Addresses',          # -- define y axis title 
                      yaxis_data_type = 'numeric',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Active Addresses', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)


# %%
# -- Transactions Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'txns'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'Daily Transactions Across Major Ecosystems'
  chart.subtitle = '7d moving average of daily transactions over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of daily transactions over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of daily transactions since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, GokuStats'
  chart.note = 'Cosmos daily transactions is combination of CosmosHub and Osmosis'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Daily Transactions',          # -- define y axis title 
                      yaxis_data_type = 'numeric',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Daily Txns', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

# %%
# -- Twitter Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'twitter'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'Twitter Followers of Major Ecosystem Main Accounts'
  chart.subtitle = '7d moving average of ecosystem main twitter accounts over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of ecosystem main twitter accounts over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of ecosystem main twitter accounts since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, GokuStats'
  chart.note = 'Only Cosmos main account followers counted. Other app chains not included.'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Twitter Followers',          # -- define y axis title 
                      yaxis_data_type = 'numeric',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Followers', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

# %%
# -- Stablecoin Charts 
plot_chains = list(chain_df.chain.unique())
plot_chains.remove('Arbitrum')
plot_chains.remove('Optimism')

plot_column = 'stable_supply'
moving_avg = 7 

for date_range in date_ranges: 
  # -- filter dataframe 
  if date_range > 900: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean()
    date_range = 'all'
  else: 
    plot_df = chain_df[chain_df['chain'].isin(plot_chains)].groupby(['date', 'chain'])[plot_column].sum().unstack().rolling(moving_avg).mean().iloc[(-1 * date_range)::]

  # -- sort df with largest chains first
  new_cols = list(plot_df.iloc[-1::].sum().sort_values(ascending = False).index)
  plot_df = plot_df[new_cols]

  # -- initialize chart
  chart = messychart(plot_df)
    
  # -- define titles
  chart.title = 'Stablecoin Supply Changes Across Major Ecosystems'
  chart.subtitle = '7d moving average of each chain stablecoin supply over the last ' + str(date_range) +'d'
  chart.subtitle = '7d moving average of each chain stablecoin supply over the last year' if date_range == 365 else chart.subtitle
  chart.subtitle = '7d moving average of each chain stablecoin supply since the start of 2021' if date_range == 'all' else chart.subtitle
  chart.source = 'Messari, DeFi Llama'
  chart.note = 'Only supply of top 12 stablecoins included'

  # -- line chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Chain Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

  # -- area chart  
  chart.filepath = filepath_chart + 'chain-' + plot_column + '-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)


