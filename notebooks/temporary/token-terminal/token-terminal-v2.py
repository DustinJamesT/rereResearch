# %%
# -- imports 
import pandas as pd
import requests
import os


# %%
# ===================
# -- Config
# ===================

report_title = 'token-terminal'

filepath_chart = '/home/runner/Messari-Reports/charts/' + report_title.lower() + '/'
filepath_data =  '/home/runner/Messari-Reports/data/'   + report_title.lower() + '/'

api_key=os.getenv('TOKEN_TERMINAL_API')



# %%
# -- get project ids 
url = 'https://api.tokenterminal.com/v2/internal/projects'

# -- call url with tokenerminal api key
response = requests.get(url, headers={'Authorization': 'Bearer ' + api_key})

# -- convert to json
project_ids_ = response.json()

# -- convert to dataframe
project_ids = pd.DataFrame(project_ids_)


# %%
# -- get historical data of all project
url = 'https://api.tokenterminal.com/v2/internal/projects/:project_id/metrics'

def getProjectData(project_id):
  # -- set params 
  params = {"timestamp_granularity": "daily", 'since': '2021-01-01'}

  # -- call url with tokenerminal api key
  response = requests.get(url.replace(':project_id', project_id), headers={'Authorization': 'Bearer ' + api_key})

  # -- convert to json
  project_data = response.json()

  # -- convert to dataframe
  project_data = pd.DataFrame(project_data)

  # -- convert timestamp to datetime without timezone
  project_data['timestamp'] = pd.to_datetime(project_data['timestamp'], utc=True).dt.tz_convert(None)

  return project_data

# %%
def getAllHistorical(projects, custom_tags = {}):
  """
  loop through project ids to get historical data for each. then combine in to a single dataframe
  """
  # -- create empty dataframe
  df = pd.DataFrame()

  # -- loop through project ids
  for project in projects:
    # -- get project data
    project_data = getProjectData(project['project_id'])

    # -- categories to df 
    if len(custom_tags) > 0:
      project_data['categories'] = str(custom_tags[ project['project_id'] ])
    else:
      project_data['categories'] = str(project['categories'])

    # -- concat dataframes
    df = pd.concat([df, project_data], axis=0)

  return df

# %%
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

for protocol in project_ids_: 

  proto_tags = protocol['categories']
  #proto_tags = proto_tags.split(',')

  # -- grab my tags 
  if protocol['project_id'] in custom_tags.keys():
    proto_tags.extend(custom_tags[ protocol['project_id'] ])

  # -- initialize tag dict for new tags 
  for tag in proto_tags: 
    if tag not in tags.keys():
      tags[tag] = []

  # -- add protocol to tag dict 
  tags[tag].append(protocol['project_id'])

  # -- add to protocol dict 
  project_tags[protocol['project_id']] = proto_tags

# %%
# -- get historical data
df = getAllHistorical(project_ids_, custom_tags=project_tags)

# %%
# -- save to csv
df.to_csv(filepath_data + 'token-terminal-v2-protocols.csv', index=False)

# %%



