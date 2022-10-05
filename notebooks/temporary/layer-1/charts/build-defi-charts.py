
import pandas as pd 

from datetime import date
import datetime

import time

import requests
import os

# -- make sure messychart in path
import sys
sys.path.append("/home/runner/Messari-Reports/scripts/messycharts/")

from messycharts import messychart

report_title = 'Layer-1'

filepath_chart = '/home/runner/Messari-Reports/charts/' + report_title.lower() + '/'
filepath_data =  '/home/runner/Messari-Reports/data/'   + report_title.lower() + '/'

today = date.today()
today_str = today.strftime("%Y-%m-%d")

date_ranges = [30,90,180,365, 999]

# -- load data 
chain_df = pd.read_csv(filepath_data + 'chain_data.csv')  
protocol_df = pd.read_csv(filepath_data + 'protocol_tvl.csv')  

# =========
# =======================================
# --- CHART CODE ================================
# =======================================
# =========

# =========================
# -- DeFi Sectors 
# =========================
p_df = protocol_df[ protocol_df.date == protocol_df.iloc[-1].date].groupby(['chain', 'category'])['tvl'].sum().unstack()

# -- sort df with largest chains first
new_cols = list(p_df.iloc[::].sum().sort_values(ascending = False).index)
p_df = p_df[new_cols]

plot_df = p_df.fillna(0).div(p_df.sum(axis=1), axis=0)
other_df = p_df.fillna(0).div(p_df.sum(axis=1), axis=0)

# -- create other column 
cols = plot_df.columns[:9]
other_cols = plot_df.columns[9:]

plot_df_ = plot_df[cols]

other_df['Other'] = other_df[other_cols].sum(axis=1)

plot_df = plot_df_.join(other_df['Other'])

plot_df.drop(plot_df[plot_df.index == 'BSC'].index, inplace= True)

del other_df

# -- intialize chart object 
chart = messychart(plot_df)

# -- define titles 
chart.title = 'DeFi Sector TVL Share Across Major Ecosystems'
chart.subtitle = 'Comparing proportional TVL across DeFi Sectors'
chart.source = 'Messari, DeFi Llama'
chart.note = 'Cosmos figures are comprised of TVL across top app chains'
#chart.date = plot_df.index[-1].strftime('%B %d, %Y')

chart.filepath = filepath_chart +'/defi/' + 'chain_sector_tvls' + '-bottom'

# -- print chart 
chart.create_slide(chart_type = 'bar_category', axis_title= 'Sector TVL Share', yaxis_data_type = 'percent', legend_layout = 'bottom', bars_different_colors = False)

# ==========================
# -- Chain DeFi Sectors 
# ==========================
skip_chains = ['BSC']

for chain_ in protocol_df.chain.unique():
  if chain_ not in skip_chains:
    for days in [30, 90, 999]: 
      # -- filter df 
      protocol_df[protocol_df.chain == chain_].groupby(['date', 'category'])['tvl'].sum().unstack()

      # -- sort df with largest chains first
      new_cols = list(p_df.iloc[::].sum().sort_values(ascending = False).index)
      p_df = p_df[new_cols]

      # -- create other col 
      cols = plot_df.columns[:8]
      other_cols = plot_df.columns[8:]

      plot_df['Other'] = plot_df[other_cols].sum(axis=1)
      plot_df.drop(columns = other_cols, inplace=True)
      
      if days <  1000:
        plot_df = plot_df.rolling(7).mean().iloc[(-1 * days)::]
      else:
        plot_df = plot_df.rolling(7).mean()

      # -- build chart 
      # -- intialize chart object 
      chart = messychart(plot_df)

      # -- define titles 
      chart.title = chain_ + ' DeFi Sector TVL Over Time'
      chart.subtitle = '7d moving average of ' + chain_ + "'s DeFi sector TVL"
      chart.source = 'Messari, DeFi Llama'
      chart.note = 'Other column sum of all other sectors' #Includes ' + other_cols[0] + ', ' + other_cols[1] + ',  ' + other_cols[2] + ' & more'
      #chart.date = plot_df.index[-1].strftime('%B %d, %Y')

      chart.filepath = '../defi/' + chain_ + '-defi-sectors-timeseries'
      chart.filepath = chart.filepath + '-all' if days > 365 else chart.filepath + '-' + str(days)

      # -- print chart 
      chart.create_slide(chart_type = 'area', 
                          axis_title= 'DeFi Sector TVL',          # -- define y axis title 
                          yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                          legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                          legend_title='Sector TVL (7d MA)', # -- defines legend title - only use with the "right" or "right_values" options 
                          digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values legend type)
