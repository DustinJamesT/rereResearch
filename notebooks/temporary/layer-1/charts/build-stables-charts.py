
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

  calc_days = 14 if date_range == 30 else 30 

  # -- line chart  
  chart.filepath = filepath_chart +'/stables/' + 'allChain-line-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'line', 
                      axis_title= 'Chain Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      calc_days = calc_days,
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)

  # -- area chart  
  chart.filepath = filepath_chart +'/stables/' + 'allChain-area-' + str(date_range) + '-rhv'
  chart.create_slide(chart_type = 'area', 
                      axis_title= 'Market Cap',          # -- define y axis title 
                      yaxis_data_type = 'dollar',       # -- defines the type: can be ['numeric', 'dollar', 'percent']. default is numeric 
                      legend_layout = 'right_values',   # -- defines the legend style and placement. options are ['bottom', 'right', 'right_values', 'None']
                      legend_title='Chain Market Cap', # -- defines legend title - only use with the "right" or "right_values" options 
                      calc_days = calc_days,
                      digits=1)                         # -- defines the number of digits in the y axis and the legend (if right_values)


