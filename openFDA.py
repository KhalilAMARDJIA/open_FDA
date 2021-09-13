import json
import math
import requests

def fda_url(query, data_base="event", count=False, field_count='', limit=1000):
    key = '&api_key=WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'
    api = f'https://api.fda.gov/device/{data_base}.json?{key}&search='

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

def general_json(query, data_base = 'event'):
    urls = fda_url(query= query, data_base= data_base)
    meta_data = get_meta(urls)
    last_updated = meta_data['last_updated']
    n_results = meta_data['results']['total']
    raw_data = url_to_json(urls)
    print("last updated in: ", last_updated, "with ", n_results, " results")
    return raw_data


data = general_json(query='in2bones', data_base= "event")

with open('openFDA_raw_data.json', 'w') as f:
    json.dump(data, f, indent= 5)

report_number, manufacturer_d_name, date_received, brand_name, product_problems, patient_problems, text_1_code, text_1, text_0_code, text_0 = [], [], [], [], [], [], [], [], [], []
for record in data:
        report_number.append(record['report_number'])
        manufacturer_d_name.append(record['device'][0]['manufacturer_d_name'])
        date_received.append(record['date_received'])
        brand_name.append(record['device'][0]['brand_name'])

        try:
            product_problems.append(record['product_problems'])
        except:
            product_problems.append("")

        try:
            patient_problems.append(record['patient'][0]['patient_problems'])
        except:
            patient_problems.append("")

        try:
            text_1_code.append(record['mdr_text'][1]['text_type_code'])

        except:
            text_1_code.append("")
        
        try:
            text_1.append(record['mdr_text'][1]['text'].lower())

        except:
            text_1.append("")

        try:
            text_0_code.append(record['mdr_text'][0]['text_type_code'])

        except:
            text_0_code.append("")

        try:
            text_0.append(record['mdr_text'][0]['text'].lower())

        except:
            text_0.append("")