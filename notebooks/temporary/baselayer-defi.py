import pandas as pd 

from datetime import date
import datetime

import time

import requests
import os

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

# ============================================================
# -- report config 
# ============================================================ 
report_title = 'Layer-1'

filepath_chart = '/home/runner/Messari-Reports/charts/' + report_title.lower() + '/'
filepath_data =  '/home/runner/Messari-Reports/data/'   + report_title.lower() + '/'

today = date.today()
today_str = today.strftime("%Y-%m-%d")

date_ranges = [30,90,180,365, 999]

# ============================================================
# -- get protocol data 
# ============================================================

# -- define chains 
chains = ['Ethereum', 'Solana', "Avalanche", "Polygon", 'Arbitrum', 'Optimism', 'Fantom', 'Near', 'BSC']
cosmos_chains = ['cosmos', 'osmosis', 'cronos', 'evmos', 'thorchain', 'kava', 'juno', 'secret', 'canto']

# -- load DeFi llama protocols 
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


# -- save data frame 
protocol_df.to_csv(filepath_data + 'protocol_tvl.csv', index=False)


# ===============================
# -- get all chain tvl and categories 
# ===============================

# -- function to get type of chain 
def getTVLtype(chain): 
  trigger_words = {
    'staking': 'staking', 
    'borrowed': 'borrowed',
    'pool2': 'pool2',
    'treasury': 'treasury',
    'masterchef': 'masterchef', # -- wtf do we call this? 
    'vesting': 'vesting'
  }

  chain_label = 'None'

  # -- check if chain contains trigger word
  for trigger, label in trigger_words.items():
    if trigger in chain: 
      if trigger != chain:
        # -- make sure not aggregated metric 
        chain_info = chain.split('-')

        if len(chain_info) > 1:
          chain_name = chain_info[0]
          chain_label = label
        else: 
          chain_name = chain 
          chain_label = label
      else:
        # -- skip aggregated metric like total borrowed tvl across all chains 
        chain_name = 'skip' 
        chain_label = 'skip'

  # -- no trigger words - probably normal chain 
  chain_name = chain 
  chain_label = 'standard'

  # -- hardcode BSC over binance 
  chain_name = 'BSC' if chain_name == 'Binance' else chain_name 
  
  return chain_name, chain_label



# -- function to get protocol tvl in my format (test)
def getProtocolTVL_allchains(slug, protocol_name, category): 
  url = 'https://api.llama.fi/protocol/' + slug 
  resp = requests.get(url)
  protocol_data = resp.json()['chainTvls']

  df_build = []

  for chain, data in protocol_data.items(): 
    # -- get type of TVL 
    chain_name, chain_label = getTVLtype(chain)

    # -- make entry if not skip labeled 
    if chain_name != 'skip':
      # -- loop through daily tvl entry and format
      for daily in data['tvl']: 

        dt_object = datetime.datetime.fromtimestamp(int(daily['date']))
        date = dt_object.strftime('%Y-%m-%d')

        df_build.append({
          'date': date, 
          'chain': chain_name,
          'ecosystem': chain_name,
          'protocol': protocol_name,
          'category': category,
          'tvl-category': chain_label,
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

  temp_df = getProtocolTVL_allchains(dl_protocol_df[protocol].slug, dl_protocol_df[protocol].name, category)

  protocol_dfs.append(temp_df)


protocol_df = pd.concat(protocol_dfs, axis=0)

# -- fix cosmos chains 
protocol_df['ecosystem'] = protocol_df.apply(lambda x: x.ecosystem if x.ecosystem not in cosmos_chains else 'Cosmos', axis=1)

# -- trim data set to 2021 and up 
protocol_df['date'] = pd.to_datetime(protocol_df['date'])
protocol_df = protocol_df[protocol_df.date.dt.year > 2020]


# -- save data frame 
protocol_df.to_csv(filepath_data + 'protocol_tvl_allchains.csv', index=False)