import requests
import json
import csv
import os
import math

dir_path = os.path.dirname(os.path.realpath(__file__))


def fda_url(query, data_base="udi", count=False, field_count='', limit=100):
    """fda_url(query = "", data_base= ["event","udi","510k"...], count= False, field_count = "", limit= 100)"""

    key = '&api_key=WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'
    api = f'https://api.fda.gov/device/{data_base}.json?{key}&search='

    if count == True:
        urls = f'{api}{query}&count={field_count}'

    elif count == False:

        meta_url = f'{api}{query}'
        JSON_re = requests.get(meta_url).json()
        number_results = JSON_re['meta']['results']['total']

        if number_results > 100:

            urls = []

            n_skips = math.ceil(number_results / 100)
            for i in range(0, n_skips):
                skip = 100*i
                url = f'{api}{query}&limit={limit}&skip={skip}'
                urls.append(url)

        else:
            skip = 0
            urls = f'{api}{query}&limit={limit}&skip={skip}'

    return urls


def get_meta(urls):
    if isinstance(urls, list):
        for url in urls:
            result = requests.get(url).json()
            meta = result['meta']
            break

    else:
        result = requests.get(urls).json()
        meta = result['meta']
    return meta


def fda_results(url):
    response = requests.get(url)
    if response.ok:
        d = json.loads(response.text)
        results = d["results"]
    else:
        results = []
    return results
