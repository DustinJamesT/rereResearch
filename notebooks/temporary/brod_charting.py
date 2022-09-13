

# Imports
from io import BytesIO
import PIL
from PIL import (
    Image,
    ImageFont,
    ImageDraw,
    PngImagePlugin
)
from datetime import date
from pyparsing import col
import requests
from copy import deepcopy
import plotly.express as px
import pandas as pd

## Have to also install kaleido if not already installed:
## pip install kaleido



########################################################################################################
############################################### Styling ################################################
########################################################################################################

#All themes, fonts, etc.
messari_fonts = {
    "Montserrat-Bold": "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Montserrat-Bold.ttf?raw=True",  # https://fonts.google.com/specimen/Montserrat?query=monts
    "Montserrat-Reg": "https://github.com/DustinJamesT/supply_curves/blob/6df2a17cdd9c5011bf205abfe7e50d498622feb2/Graphics/Montserrat-Regular.ttf?raw=True",
    "Montserrat-SemiBold": "https://github.com/DustinJamesT/supply_curves/blob/e4fac393fca3d51ab22d30f2d9874334bb2b7412/Graphics/Montserrat-SemiBold.ttf?raw=True",
    "Open-Sans-Reg": "https://github.com/DustinJamesT/supply_curves/blob/d04f226559f7b5970160606b357701efe3214b47/OpenSans-Regular.ttf?raw=True",  # https://fonts.google.com/specimen/Open+Sans
    "Open-Sans-semiBold": "https://github.com/DustinJamesT/supply_curves/blob/01263a2b5fe88d376e3431668c155b1d208c80d3/OpenSans-SemiBold.ttf?raw=True",
    "Open-Sans-Italic": "https://github.com/DustinJamesT/supply_curves/blob/c7f0bf1c2cfab6382bb8ec1ad812d26dcc562cad/Graphics/OpenSans-Italic.ttf?raw=True",
}

fonts = {}
for font, url in messari_fonts.items():
    font_request = requests.get(url)
    font_file = font_request.content

    fonts[font] = font_file

colors_dict = {
    'main_colors': [
        "#231DC5",
        "#1B80F3",
        "#00D1FF",
        "#7000FF",
        "#A030E5",
        "#CE66FF",
        "#16B65F",
        "#00E778",
        "#59FFCD",
        "#FFC700",
        "#FFDD64",
        "#FFF384",
        "#F5E391",
        "#F3B09B",
    ],
    # NOTE: old & out of favor colors
    'alt_colors' : [
        "#3A6495",
        "#5B8EDC",
        "#8ED7E1",
        "#B5D987",
        "#F09837",
        "#ED6E69",
        "#3668BB",
        "#40838D",
        "#608435",
        "#784D17",
    ]
}


theme_dict = {
    'light': {
        'color_pallet': colors_dict['main_colors'], # Main color pallet
        'border_color': '#232629', # off black
        'gridline_color': "#ECF0F4",  # light grey
        'text_color': "#232629",  # off black
        'title_color': "#1D1F22",  # basically black
        'subtext_color': "#A6B3C1",  # grey - used for sub title and for date
        'background_url': "https://github.com/DustinJamesT/supply_curves/blob/f940adff54e52ac13a577bb38554cffdf18b1221/Graphics/Messari_blank_light.png?raw=True", ##does not have all text (ie: Source:, Date as of:, etc.)
    },
    'dark': {
        'color_pallet': colors_dict['main_colors'], # Main color pallet
        'border_color': '#CFDBE7', # off white
        'gridline_color': "#3D434A",  # dark grey
        'text_color': "#CFDBE7",
        'title_color': "#F3F7FB",  # basically white
        'subtext_color': "#A6B3C1",  # grey - used for sub title and for date
        #'background': dark_background,
        'background_url': "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Messari_slide_clean.png?raw=True",
    }
}

yaxis_fmt_dict = {
    'percentage':".2%",
    'numeric':None
}

########################################################################################################
############################################# Utilities ################################################
########################################################################################################

## Function to overlay plot png over messari background slide
## Used within charting function and inherits args passed to the charting function

def create_output_image(filepath, theme, chart_title, chart_subtitle, chart_source, chart_note, pie_chart):

    # COMBINE IMAGES
    foreground = Image.open(f'{filepath}-raw.png')

    response = requests.get(theme_dict[theme]['background_url'])
    background = Image.open(BytesIO(response.content))

    #adjust formatting for pie_charts
    if pie_chart == True:
        background.paste(foreground, (50, 140), foreground)
    elif pie_chart == False:
        background.paste(foreground, (50, 100), foreground)

    draw = ImageDraw.Draw(background)

    today = date.today() 
    date_text = today.strftime("%b %d, %Y")

    text_data = {
        'title':    {'text': chart_title,
                    'font': 'Montserrat-Bold','font_size': 42, 'x': 161, 'y':40, 'fill': theme_dict[theme]['title_color']}, # dont change this row
                
        'subtitle': {'text': chart_subtitle,
                    'font': 'Open-Sans-Reg' ,'font_size': 24, 'x': 165, 'y':92, 'fill': theme_dict[theme]['subtext_color']},
                
        'source':   {'text': chart_source,
                    'font': 'Open-Sans-Reg','font_size': 20, 'x': 132, 'y':792, 'fill': theme_dict[theme]['text_color']},
                
        'note':     {'text': chart_note,
                    'font': 'Open-Sans-Reg' ,'font_size': 20, 'x': 113, 'y':838, 'fill': theme_dict[theme]['text_color']},
                
        'date':     {'text': date_text,
                    'font': 'Open-Sans-semiBold','font_size': 20, 'x': 1334, 'y':831, 'fill': theme_dict[theme]['subtext_color']},
    }

    # draw text items
    for textfield, data in text_data.items():
        font = ImageFont.truetype(
            BytesIO(fonts[data["font"]]), data["font_size"]
        )
        draw.text((data['x'], data['y']), data['text'], data['fill'], font=font)
    return background



########################################################################################################
############################################### Charting ###############################################
########################################################################################################




########################################## Timeseries Charts ###########################################

#This function charts a dataframe with a timeseries index. Details of the arguments to input are below:

#df: the dataframe containing the data to be plotted
#chart_type: 'area', 'line', or 'bar' (type: string)
#theme: 'light' or 'dark' (type: string) NOTE: we need to recreate the 'light' slide so only use 'dark for now 
#chart_title: the title of the chart (type: string)
#chart_subtitle: the subtitle of the chart (type: string)
#chart_source: the source of the data (type: string)
#chart_note: A note displayed at the bottom of the chart (type: string)
#legend_title: Title of the legend (type: string), if none is desired type None
#legend_placement: 'bottom' or 'right' (type: string)
#yaxis_data_type: 'percentage' or 'numeric' (type: string) (formats y axis ticks. If values are percentages, will format and add % sign. If values are millions, billions, etc. will format and add M or B suffix)
#ytick_dollar_sign: True or False (type: Boolean) (if True, a $ prefix is added to y axis tick labels. If false, no dollar sign is added. Can add other symbols in the future if needed)
#yaxis_title: the title of the y-axis, (type: string)
#filepath: the name of the final image file (type: string)


def create_timeseries_chart(df: pd.DataFrame, chart_source: str, filepath: str, chart_type: str='line', theme: str='dark', \
    chart_title: str='', chart_subtitle: str='', chart_note: str='', legend_title: str='', legend_placement: str='right', \
    yaxis_data_type: str='numeric', ytick_dollar_sign: bool=False, yaxis_title: str='') -> PIL.PngImagePlugin.PngImageFile:

    #handling logic, print error statement and revert to default ARGS
    if chart_type not in ['area', 'line', 'bar']:
        response = print("Incorrect input for chart_type argument. Selections are: 'area', 'bar', or 'line'. Defaulting to 'line'.")
        print(response) 
        chart_type = 'line'
    if theme not in ['dark', 'light']:
        response = print("Incorrect input for theme argument. Selections are: 'dark' or 'light'. Defaulting to 'dark'.")
        print(response) 
        theme = 'dark'
    if legend_placement not in ['right', 'bottom']:
        response = print("Incorrect input for legend_placement argument. Selections are: 'right' or 'bottom'. Defaulting to 'right'.")
        print(response) 
        legend_placement = 'right'
    if yaxis_data_type not in ['numeric', 'percentage']:
        response = print("Incorrect input for yaxis_data_type argument. Selections are: 'numeric' or 'percentage'. Defaulting to 'numeric'.")
        yaxis_data_type = 'numeric'
    if ytick_dollar_sign not in [True, False]:
        response = print("Incorrect input for ytick_dollar_sign argument. Selections are: True or False. Defaulting to False.")
        ytick_dollar_sign = False
     
    #chart type selection
    if chart_type == 'area':
        fig = px.area(df, color_discrete_sequence=theme_dict[theme]['color_pallet'])
        fig.update_traces(line={'width':0})
    elif chart_type == 'line':
        fig = px.line(df, color_discrete_sequence=theme_dict[theme]['color_pallet'])
        fig.update_traces(line={'width':3})
    elif chart_type == 'bar':
        fig = px.bar(df, color_discrete_sequence=theme_dict[theme]['color_pallet'])

    #legend placement
    if legend_placement == 'bottom':
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            'yaxis_title':yaxis_title,
            'legend_title':legend_title,
            'font_color':theme_dict[theme]['text_color'],
            'font_size':20,
            'width':1500,
            'height':675,
            'legend_orientation':"h", #needed for legend center bottom
            'legend_x':.5, #needed for legend center bottom
            'legend_xanchor':'center' #needed for legend center bottom
        })
    elif legend_placement == 'right':
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            'yaxis_title':yaxis_title,
            'legend_title':legend_title,
            'font_color':theme_dict[theme]['text_color'],
            'font_size':20,
            'width':1500,
            'height':675
        })
    
    #ytick prefix 
    if ytick_dollar_sign == True:
        fig.update_layout({'yaxis_tickprefix':"$"})
    elif ytick_dollar_sign == False:
        fig.update_layout({'yaxis_tickprefix':""})
    
    #xaxes formatting
    fig.update_xaxes(
        showgrid=False,
        linecolor=theme_dict[theme]['border_color']
    )
    #yaxes formatting
    fig.update_yaxes(
        gridcolor=theme_dict[theme]['gridline_color'],
        linecolor=theme_dict[theme]['border_color'],
        zeroline=False,
        tickformat=yaxis_fmt_dict[yaxis_data_type]
    )

    #write image w/ filepath name
    fig.write_image(f'{filepath}-raw.png')
    
    #create final image by overlaying png onto Messari slide
    background = create_output_image(filepath=filepath, theme=theme, chart_title=chart_title, chart_subtitle=chart_subtitle, chart_source=chart_source, chart_note=chart_note, pie_chart=False)
    
    #save final image locally
    background.save(f'{filepath}.png')
    
    return background
        

########################################## Categorical Charts ##########################################

## These functions chart categorical data as a bar chart or a pie chart. 
## The bar chart function accepts the df index for the x axis values


#df: the dataframe containing the data to be plotted
#bars_different_colors: True or False (type: Boolean)
#theme: 'light' or 'dark' (type: string) NOTE: we need to recreate the 'light' slide so only use 'dark for now 
#chart_title: the title of the chart (type: string)
#chart_subtitle: the subtitle of the chart (type: string)
#chart_source: the source of the data (type: string)
#chart_note: A note displayed at the bottom of the chart (type: string)
#legend: True or False (type: Boolean)
#legend_title: Title of the legend (type: string), if none is desired type None
#yaxis_data_type: 'percentage' or 'numeric' (type: string) (formats y axis ticks. If values are percentages, will format and add % sign. If values are millions, billions, etc. will format and add M or B suffix)
#ytick_dollar_sign: True or False (type: Boolean) (if True, a $ prefix is added to y axis tick labels. If false, no dollar sign is added. Can add other symbols in the future if needed)
#yaxis_title: the title of the y-axis, (type: string)
#filepath: the name of the final image file (type: string)

def create_categorical_bar_chart(df: pd.DataFrame, chart_source: str, filepath: str, bars_different_colors: bool=True, theme: str='dark', \
    chart_title: str='', chart_subtitle: str='', chart_note: str='', legend: bool=False, legend_title: str='', \
    yaxis_data_type: str='numeric', ytick_dollar_sign: bool=False, yaxis_title: str='') -> PIL.PngImagePlugin.PngImageFile:    

    #handling logic, print error statement and revert to default ARGS
    if bars_different_colors not in [True, False]:
        print("Incorrect input for bars_different_colors argument. Selections are: True or False. Defaulting to True.")
        bars_different_colors = True
    if theme not in ['dark', 'light']:
        print("Incorrect input for theme argument. Selections are: 'dark' or 'light'. Defaulting to 'dark'.")
        theme = 'dark'
    if legend not in [True, False]:
        print("Incorrect input for legend argument. Selections are: True or False. Defaulting to False.")
        legend = False
    if yaxis_data_type not in ['numeric', 'percentage']:
        print("Incorrect input for yaxis_data_type argument. Selections are: 'numeric' or 'percentage'. Defaulting to 'numeric'.")
        yaxis_data_type = 'numeric'
    if ytick_dollar_sign not in [True, False]:
        print("Incorrect input for ytick_dollar_sign argument. Selections are: True or False. Defaulting to False.")
        ytick_dollar_sign = False


    if bars_different_colors == True:
        fig = px.bar(df, color=df.index, color_discrete_sequence=theme_dict[theme]['color_pallet'])
    elif bars_different_colors == False:
        fig = px.bar(df, color_discrete_sequence=theme_dict[theme]['color_pallet'])

    if legend == False:
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            'yaxis_title':yaxis_title,
            'font_color':theme_dict[theme]['text_color'],
            'font_size':20,
            'width':1500,
            'height':675,
            'showlegend':False
        })
    elif legend == True:
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            'yaxis_title':yaxis_title,
            'legend_title':legend_title,
            'font_color':theme_dict[theme]['text_color'],
            'font_size':20,
            'width':1500,
            'height':675
        })
    
    if ytick_dollar_sign == True:
        fig.update_layout({'yaxis_tickprefix':"$"})
    elif ytick_dollar_sign == False:
        fig.update_layout({'yaxis_tickprefix':""})
    
    fig.update_xaxes(
        showgrid=False,
        linecolor=theme_dict[theme]['border_color']
    )

    fig.update_yaxes(
        gridcolor=theme_dict[theme]['gridline_color'],
        linecolor=theme_dict[theme]['border_color'],
        zeroline=False,
        tickformat=yaxis_fmt_dict[yaxis_data_type]
    )

    number_of_bars = len(fig.data)
    bar_range = range(0, number_of_bars, 1)
    range_list = list(bar_range)
    for i in range_list:
        fig.data[i]["marker"]['line']['width'] = 0


    fig.write_image(f'{filepath}-raw.png')
    
    background = create_output_image(filepath=filepath, theme=theme, chart_title=chart_title, chart_subtitle=chart_subtitle, chart_source=chart_source, chart_note=chart_note, pie_chart=False)
    
    background.save(f'{filepath}.png')
    
    return background



## The below function plots a pie chart. It needs to be passed the name of the column containing the values (values ARG).
## It inherits the df index for the names ARG (categories, ie: each slice of the pie chart)

#df: the dataframe containing the data to be plotted
#values: the dataframe column containing the values to be charted (type: str)
#theme: 'light' or 'dark' (type: string) NOTE: we need to recreate the 'light' slide so only use 'dark for now 
#chart_title: the title of the chart (type: string)
#chart_subtitle: the subtitle of the chart (type: string)
#chart_source: the source of the data (type: string)
#chart_note: A note displayed at the bottom of the chart (type: string)
#filepath: the name of the final image file (type: string)

def create_pie_chart(df: pd.DataFrame, chart_source: str, filepath: str, values: str, theme: str='dark', \
    chart_title: str='', chart_subtitle: str='', chart_note: str='', legend_title: str='') -> PIL.PngImagePlugin.PngImageFile:    

    if theme not in ['dark', 'light']:
        print("Incorrect input for theme argument. Selections are: 'dark' or 'light'. Defaulting to 'dark'.")
        theme = 'dark'
    
    fig = px.pie(df, values=values, names=df.index, hole=.4, color_discrete_sequence=theme_dict['dark']['color_pallet'])
    fig.update_layout({
                'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                'legend_title':legend_title,
                'font_color':theme_dict['dark']['text_color'],
                'font_size':24,
                'width':1450,
                'height':625
            })

    fig.write_image(f'{filepath}-raw.png')
    background = create_output_image(filepath=filepath, theme='dark', chart_title=chart_title, chart_subtitle=chart_subtitle, chart_source=chart_source, chart_note=chart_note, pie_chart=True)

    background.save(f'{filepath}.png')
    
    return background
