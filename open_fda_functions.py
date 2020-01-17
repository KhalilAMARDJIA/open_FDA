import requests
import pandas as pd
import yaml
from flask import json

def get_results(url):
    response = requests.get(url)
    if response.ok:
        d = json.loads(response.text)
        results = d["results"]
    else:
        results = []
    return results

def get_meta(url):
    response = requests.get(url)
    d = json.loads(response.text)
    meta = d["meta"]
    meta = pd.DataFrame(meta)
    return meta


def fda_url(query, count = False, field_count = '', limit = 100, skip = 0):
    key = '&api_key=WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'
    api = f'https://api.fda.gov/device/event.json?{key}&search='
    if count == True:
        url = f'{api}{query}&count={field_count}'
    elif count == False:
        url = f'{api}{query}&limit={limit}&skip={skip}'
    return url