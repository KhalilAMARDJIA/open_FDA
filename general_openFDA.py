import json
import math
import requests

def fda_url(query, database="event", count=False, field_count='', limit=1000):
    api_key = '&api_key=WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'
    base_url = f'https://api.fda.gov/device/{database}.json?{api_key}&search='

    if count:
        url = f'{base_url}{query}&count={field_count}'
    else:
        meta_url = f'{base_url}{query}'
        json_re = requests.get(meta_url).json()
        number_results = json_re['meta']['results']['total']

        if number_results > 1000:
            n_skips = math.ceil(number_results / 1000)
            urls = [f'{base_url}{query}&limit={limit}&skip={1000*i}' for i in range(n_skips)]
        else:
            urls = [f'{base_url}{query}&limit={limit}&skip=0']

        url = urls

    return url

def get_meta(urls):
    if isinstance(urls, list):
        url = urls[0]
    else:
        url = urls

    result = requests.get(url).json()
    meta = result['meta']

    return meta

def fda_results(url):
    response = requests.get(url)
    if response.ok:
        data = json.loads(response.text)
        results = data["results"]
    else:
        results = []

    return results

def urls_to_json(urls):
    json_re = []
    for url in urls:
        unique_json = fda_results(url)
        json_re.extend(unique_json)

    return json_re

def general_json(query, database='event'):
    urls = fda_url(query=query, database=database)
    meta_data = get_meta(urls)
    last_updated = meta_data['last_updated']
    n_results = meta_data['results']['total']
    raw_data = urls_to_json(urls)

    print(f'From the {database} last updated in: {last_updated} with: {n_results} results')

    with open('openFDA_raw_data.json', 'w') as f:
        json.dump(raw_data, f, indent=5)

    return raw_data, database
