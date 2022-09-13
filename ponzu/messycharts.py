# -- this class defines chart creation class used to generate publishable slides of pandas charts 

# == table of contents 

# --- 1.00 - imports
# --- 2.00 - class definition 
# ----- 2.01 - initialization 
# ----- 2.02 - build chart  


# == 1.00 imports 
import pandas as pd

import requests 

import math 

from matplotlib import pyplot as plt

import matplotlib.ticker as ticker
import matplotlib.ticker as mtick

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

import matplotlib.dates as mdates
import numpy as np

from io import BytesIO

# == 2.00 class definition
class messychart():

  # 2.01 - initialization 
  def __init__(self, df, theme = 'dark', layout = 'full_width_bottom'):
    # -- dataframe
    self.df = df

    # -- slide variables 
    self.name = ''
    self.title = ''
    self.subtitle = ''
    self.date = ''
    self.note = ''
    self.sources = ''

    # -- chart variables
    self.scale_factor = 4 

    self.axis_label = ''
    self.axis_format = ''
    self.secondary_axis_label = ''
    self.secondary_axis_format = ''
    self.side_legend_adj = 0
    self.side_legend_decimals = -1 # -- if 0 or greater it overrides the axis format for the side legend 
    self.filepath_raw = ''
    self.plot = None 
    self.color_pallet = ['#3A6495', '#5B8EDC', '#8ED7E1','#B5D987','#F09837','#ED6E69','#3668BB','#40838D','#608435','#784D17' ] # this is shit. please design a better one TODO

    # -- chart layouts 
    chart_layouts = {
      'full_width_float':        {'figsize_x': 17, 'figsize_y': 7.5, 'loc_x':-50, 'loc_y': 50, 'legend_style': 'pandas_default'}, 
      'full_width_bottom': {'figsize_x': 17, 'figsize_y': 7,   'loc_x':-50, 'loc_y': 50, 'legend_style': 'pandas_bottom'},
      'three_quarter':     {'figsize_x': 14, 'figsize_y': 7.5, 'loc_x':-30, 'loc_y': 55, 'legend_style': 'custom_side'}
    }

    # -- set defualt chart 
    self.layout = 'full_width_bottom' if layout not in chart_layouts.keys() else layout
    self.legend_items = []

    self.legend_style = chart_layouts[self.layout]['legend_style']
    self.figsize_x =    chart_layouts[self.layout]['figsize_x']
    self.figsize_y =    chart_layouts[self.layout]['figsize_y']
    self.loc_x =        chart_layouts[self.layout]['loc_x'] 
    self.loc_y =        chart_layouts[self.layout]['loc_y']

    # -- theme color schemes 
    if theme == 'light': 
      self.boarder_color = '#232629'  #off black
      self.gridline_color = '#ECF0F4' #light grey 
      self.text_color = '#232629'     #off black
      self.title_color = '#1D1F22'    #basically black
      self.subtext_color = '#A6B3C1'  #grey - used for sub title and for date 

      response = requests.get('https://github.com/DustinJamesT/supply_curves/blob/f940adff54e52ac13a577bb38554cffdf18b1221/Graphics/Messari_blank_light.png?raw=True')
      self.background = Image.open(BytesIO(response.content))
      self.final_image = None

    elif 'dark' in theme: 
      self.boarder_color = '#CFDBE7'  #off white 
      self.gridline_color = '#3D434A' #dark grey
      self.text_color = '#CFDBE7' if 'table' not in self.layout else '#F3F7FB'
      self.title_color = '#F3F7FB'    #basically white 
      self.subtext_color = '#A6B3C1'  #grey - used for sub title and for date 

      # TODO put the image in a messari github or AWS S3 
      response = requests.get('https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Messari_slide_clean.png?raw=True')
      self.background = Image.open(BytesIO(response.content))
      self.final_image = None


  # -- define fonts ---
    # TODO put these in a messari github or AWS S3 
    messari_fonts_ = {
        'Montserrat-Bold':    "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Montserrat-Bold.ttf?raw=True", #https://fonts.google.com/specimen/Montserrat?query=monts
        'Montserrat-Reg':     "https://github.com/DustinJamesT/supply_curves/blob/6df2a17cdd9c5011bf205abfe7e50d498622feb2/Graphics/Montserrat-Regular.ttf?raw=True",
        'Montserrat-SemiBold':"https://github.com/DustinJamesT/supply_curves/blob/e4fac393fca3d51ab22d30f2d9874334bb2b7412/Graphics/Montserrat-SemiBold.ttf?raw=True",
        'Open-Sans-Reg':      "https://github.com/DustinJamesT/supply_curves/blob/d04f226559f7b5970160606b357701efe3214b47/OpenSans-Regular.ttf?raw=True", #https://fonts.google.com/specimen/Open+Sans
        'Open-Sans-semiBold': "https://github.com/DustinJamesT/supply_curves/blob/01263a2b5fe88d376e3431668c155b1d208c80d3/OpenSans-SemiBold.ttf?raw=True",
        'Open-Sans-Italic':   "https://github.com/DustinJamesT/supply_curves/blob/c7f0bf1c2cfab6382bb8ec1ad812d26dcc562cad/Graphics/OpenSans-Italic.ttf?raw=True"
    }

    self.fonts = {}

    for font, url in messari_fonts_.items():
      font_request = requests.get(url)
      font_file = font_request.content

      self.fonts[font] = font_file


  # 2.02 - build chart 
  def buildChart(self, kind = 'line', secondary_column = '', axis_label_rotation = 0): 

    # -- define plot columns
    if secondary_column in self.df.columns:
      plot_cols = list(self.df.columns)
      plot_cols.remove(secondary_column)
    else:
      plot_cols = list(self.df.columns)

    # -- set chart config based on type 
    chart_config = {
      'line': {'linewidth': 3, 'stacked': False}, 
      'bar':  {'linewidth': 0, 'stacked': True}, 
      'area': {'linewidth': 0, 'stacked': False}
    }

    # -- build chart 
    ax1 = self.df[plot_cols].plot( figsize = (self.figsize_x, self.figsize_y),
                                    legend = True if 'pandas' in self.legend_style else False,
                                    kind = kind,
                                    stacked = chart_config[kind]['bar'],
                                    color = self.color_pallet[:len(plot_cols)], 
                                    rot= axis_label_rotation,
                                    linewidth = chart_config[kind]['linewidth'], 
                                    fontsize = 14 
                                    )

    if secondary_column in self.df.columns:
      self.df[plot_cols].plot(  kind = 'line',
                                color = self.color_pallet[len(plot_cols):len(self.df.columns)], 
                                rot= axis_label_rotation,
                                linewidth = chart_config['line']['linewidth'], 
                                fontsize = 14, 
                                secondary_y = True,
                                ax = ax1 
                                )


    # -- style chart 
    # -- Set axis colors and remove top + right boarders
    ax1.spines['bottom'].set_color(self.boarder_color) 
    ax1.spines['left'].set_color(self.boarder_color)

    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)

    # -- change tick colors to match axis color 
    ax1.tick_params(axis='x', colors= self.boarder_color,which='both')
    ax1.tick_params(axis='y', colors= self.boarder_color,which='both')

    # -- turn off minor ticks 
    ax1.tick_params(axis='x',which='minor',bottom='off')

    # -- format y-axis 
    if len(self.axis_format) > 0:
      tick = mtick.StrMethodFormatter(self.axis_format)
      ax1.yaxis.set_major_formatter(tick) 

    ax1.set_ylabel(self.axis_label, fontsize=14)
    ax1.yaxis.label.set_color(self.text_color)

    # -- remove x-axis label thats auto inserted 
    ax1.set_xlabel("")

    # -- set gridlines
    ax1.set_axisbelow(True)
    ax1.grid(axis='y', color= self.gridline_color)

    # -- save output 
    self.plot = ax1
    self.filepath_raw = 'raw_charts/' + self.name + '.png'
    #plt.savefig(self.filepath_raw, transparent=True, dpi = 100)










    



