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
#tokenterminal = TokenTerminal(api_key='610b30be-e8b5-4b64-a27d-d59c94132ee4')

# ===================
# -- Config
# ===================

report_title = 'tokenterminal'

filepath_chart = '/home/runner/Messari-Reports/charts/' + report_title.lower() + '/'
filepath_data =  '/home/runner/Messari-Reports/data/'   + report_title.lower() + '/'

today = date.today()
today_str = today.strftime("%Y-%m-%d")

date_ranges = [30,90,180,365, 999]

# -- get protocol info 
all_protocol_data = tokenterminal.get_all_protocol_data()

# -- set custom tags 
custom_tags = {
  'livepeer': ['Web3 Infrastructure', 'File Storage'],
  'helium': ['Web3 Infrastructure', 'DeWi'],
  'the-graph': ['Web3 Infrastructure'],
  'instadapp': ['DeFi', 'Services'],
  'keeperdao': ['MEV'],
  'lido-finance': ['DeFi', 'Staking'],
  'pooltogether': ['DeFi'],
  'synthetix': ['DeFi', 'Synthetics'],
  'uma': ['DeFi', 'Synthetics']
}

# -- build tag dictionary 
tags = {}
project_tags = {}

for protocol in all_protocol_data.columns: 

  proto_tags = all_protocol_data[protocol].loc['category_tags']
  proto_tags = proto_tags.split(',')

  # -- grab my tags 
  if protocol in custom_tags.keys():
    proto_tags.extend(custom_tags[protocol])

  # -- initialize tag dict for new tags 
  for tag in proto_tags: 
    if tag not in tags.keys():
      tags[tag] = []

  # -- add protocol to tag dict 
  tags[tag].append(protocol)

  # -- add to protocol dict 
  project_tags[protocol] = proto_tags


# -- wrapper for getting TT data 
def getTT(protocol):
  start_date = "2021-01-01"
  end_date = today_str
  protocol_data = tokenterminal.get_protocol_data([protocol], start_date=start_date, end_date=end_date)

  protocol_data.columns = protocol_data.columns.droplevel()

  cols = ['date']
  cols.extend(list(protocol_data.columns))

  protocol_data.reset_index(inplace=True)

  protocol_data.columns = cols

  return protocol_data


# -- build data set 
dfs = []

for protocol in all_protocol_data.columns:
  # -- get data 
  temp_df = getTT(protocol)

  # -- add tags 
  temp_df['tags'] = str(project_tags[protocol])

  # -- store df 
  dfs.append(temp_df)

# -- combine to one df 
protocol_df = pd.concat(dfs, axis=0)



# -- save dataset 
protocol_df.to_csv(filepath_data + 'tokenTerminal_protocols.csv', index=False)