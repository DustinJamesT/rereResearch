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

# ============================================================
# -- get protocol data 
# ============================================================

dl_protocol_df = defillama.get_protocols()

tvl_cutoff = 1000000
categories = list(dl_protocol_df.loc['category'].unique())

categories.remove('Chain')
categories.remove('Bridge')

# -- filter protocols 
dl_protocol_df = dl_protocol_df.loc[:,dl_protocol_df.loc['category',:].isin(categories)]
dl_protocol_df = dl_protocol_df.loc[:,dl_protocol_df.loc['tvl',:] > tvl_cutoff]

# -- condense categories 
remap_categories = {
  'CDP': 'Stables', 
  'Algo-Stables': 'Stables', 
  'Yield Aggregator': 'Yield', 
  'NFT Marketplace': 'NFT Services', 
  'NFT Lending': 'NFT Services'
}

# -- function to get protocol tvl in my format 
def getProtocolTVL(slug, valid_chains, protocol_name, category): 
  url = 'https://api.llama.fi/protocol/' + slug 
  resp = requests.get(url)
  protocol_data = resp.json()['chainTvls']

  df_build = []

  for chain, data in protocol_data.items(): 
    
    chain = 'BSC' if chain == 'Binance' else chain 

    if chain in valid_chains:
      for daily in data['tvl']: 

        dt_object = datetime.datetime.fromtimestamp(int(daily['date']))
        date = dt_object.strftime('%Y-%m-%d')

        df_build.append({
          'date': date, 
          'chain': chain,
          'protocol': protocol_name,
          'category': category,
          'tvl': daily['totalLiquidityUSD']
        })

  df = pd.DataFrame(df_build)
  return df 


# -- build protocol tvl df 
protocol_dfs = []

valid_chains = chains[:]
cosmos_chains = [ch.capitalize() for ch in cosmos_chains]
valid_chains.extend(cosmos_chains)

for protocol in dl_protocol_df.columns:
  category = dl_protocol_df[protocol].category
  category = category if category not in remap_categories.keys() else remap_categories[category]

  temp_df = getProtocolTVL(dl_protocol_df[protocol].slug, valid_chains, dl_protocol_df[protocol].name, category)

  protocol_dfs.append(temp_df)


protocol_df = pd.concat(protocol_dfs, axis=0)

# -- fix cosmos chains 
protocol_df['chain'] = protocol_df.apply(lambda x: x.chain if x.chain not in cosmos_chains else 'Cosmos', axis=1)

# -- trim data set to 2021 and up 
protocol_df['date'] = pd.to_datetime(protocol_df['date'])
protocol_df = protocol_df[protocol_df.date.dt.year > 2020]


# %%
# -- save output 
chain_df.to_csv(filepath_data + 'chain_data.csv', index=False)
stables_df.to_csv(filepath_data + 'chain_stables.csv', index=False)
protocol_df.to_csv(filepath_data + 'protocol_tvl.csv', index=False)
