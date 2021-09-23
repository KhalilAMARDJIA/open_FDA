import json
import math
import requests

def fda_url(query, database="event", count=False, field_count='', limit=1000):
    key = '&api_key=WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'
    api = f'https://api.fda.gov/device/{database}.json?{key}&search='

    if count == True:
        urls = f'{api}{query}&count={field_count}'

    elif count == False:
        meta_url = f'{api}{query}'
        JSON_re = requests.get(meta_url).json()
        number_results = JSON_re['meta']['results']['total']


        if number_results > 1000:
            urls = []
            n_skips = math.ceil(number_results / 1000)
            for i in range(0, n_skips):
                skip = 1000*i
                url = f'{api}{query}&limit={limit}&skip={skip}'
                urls.append(url)

        else:
            skip = 0
            urls = f'{api}{query}&limit={limit}&skip={skip}'

    print(urls)
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

def url_to_json(urls):
    if isinstance(urls, list):
        json_re = []
        for url in urls:
            unique_json = fda_results(url)
            json_re.extend(unique_json)

    else:
        json_re = fda_results(urls)
    
    return json_re

def general_json(query, database = 'event'):
    urls = fda_url(query= query, database= database)
    meta_data = get_meta(urls)
    last_updated = meta_data['last_updated']
    n_results = meta_data['results']['total']
    raw_data = url_to_json(urls)
    print(
        f'From the {database} last updated in: {last_updated} with : {n_results} results'
)

    with open('openFDA_raw_data.json', 'w') as f:
        json.dump(raw_data, f, indent= 5)

    return raw_data, database