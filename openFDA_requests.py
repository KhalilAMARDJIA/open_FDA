import requests
import pandas as pd
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
    return d["meta"]

def text_results(url):
    results = get_results(url)
    df = pd.io.json.json_normalize(results,"mdr_text",["report_number","product_problems","event_type", "date_received"],errors = "ignore")
    
    # do not do anything more because datetime is not serializable
    return df

def device_results(url):
    results = get_results(url)
    df = pd.io.json.json_normalize(results,"device",["product_problems", "report_number"], errors = "ignore")
    # do not do anything more because datetime is not serializable
    return df

openFDA = "https://api.fda.gov/"
api_endpoint = "device/event.json?"
api_key = "WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9"

url_prefix = f"{openFDA}{api_endpoint}api_key={api_key}"

def text_table(all_filds ,year_start = 1991 , year_end = 2020):
    date_start = f"{year_start}-01-01"
    date_end = f"{year_end}-12-31"
    limit = 100

    url = f'{url_prefix}&search=date_received:[{date_start}+TO+{date_end}]+AND+{all_filds}&limit={limit}'
    print(url)
    df = text_results(url)
    return df 

def device_table(all_filds ,year_start = 1991 , year_end = 2020):
    date_start = f"{year_start}-01-01"
    date_end = f"{year_end}-12-31"
    limit = 100

    url = f'{url_prefix}&search=date_received:[{date_start}+TO+{date_end}]+AND+{all_filds}&limit={limit}'
    print(url)
    df = device_results(url)
    return df 

def count_fields(query_search, search_in, field):
    limit = 1000
    key = 'bvVrs5qc62pxyTDe3gFDSorYj93Hlb0IpqKlalsD'
    data_base = f'https://api.fda.gov/device/event.json?api_key={key}&search='
    url = f'{data_base}{search_in}{query_search}&limit={limit}&count={field}'
    return(url)