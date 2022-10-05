import aiohttp
import asyncio

import pandas as pd 
import datetime 

protocol_df = 'did nothing'
print('--- Start ---')

chains = ['Ethereum', 'Solana', "Avalanche", "Polygon", 'Arbitrum', 'Optimism', 'Fantom', 'Near', 'BSC']
cosmos_chains = ['cosmos', 'osmosis', 'cronos', 'evmos', 'thorchain', 'kava', 'juno', 'secret', 'canto', 'crescent', 'terra classic', 'terra2', 'sifchain']

print('------- get defi llama data with messari')
from messari.defillama import DeFiLlama
defillama = DeFiLlama()


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
async def getProtocolTVL_async(session, slug, valid_chains, protocol_name, category): 
  url = 'https://api.llama.fi/protocol/' + slug 
  async with session.get(url) as resp:
    #resp = requests.get(url)
    protocol_data = await resp.json()#['chainTvls']

    df_build = []

    for chain, data in protocol_data['chainTvls'].items(): 
      
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
async def get_protocol_df():
  async with aiohttp.ClientSession() as session:
    protocol_dfs_task = []

    cosmos_chains = ['cosmos', 'osmosis', 'cronos', 'evmos', 'thorchain', 'kava', 'juno', 'secret', 'canto', 'crescent', 'terra classic', 'terra2', 'sifchain']

    valid_chains = chains[:]
    cosmos_chains = [ch.capitalize() for ch in cosmos_chains]
    valid_chains.extend(cosmos_chains)

    for protocol in dl_protocol_df.columns:
      category = dl_protocol_df[protocol].category
      category = category if category not in remap_categories.keys() else remap_categories[category]

      #temp_df = getProtocolTVL(dl_protocol_df[protocol].slug, valid_chains, dl_protocol_df[protocol].name, category)

      protocol_dfs_task.append(
        asyncio.ensure_future(getProtocolTVL_async(session, dl_protocol_df[protocol].slug, valid_chains, dl_protocol_df[protocol].name, category))
      )

    protocol_dfs = await asyncio.gather(*protocol_dfs_task)

    protocol_df = pd.concat(protocol_dfs, axis=0)
    return protocol_df

# -- test 
protocol_df = asyncio.run(get_protocol_df())
print(protocol_df.head())