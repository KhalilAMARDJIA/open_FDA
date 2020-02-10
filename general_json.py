import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import openFDA_url as fda
import json

update_date = fda.get_meta('https://api.fda.gov/device/event.json?search=in2bones')['last_updated']

def url_to_json(urls):
    if isinstance(urls, list):
        json_re = []
        for url in urls:
            unique_json = fda.fda_results(url)
            json_re.extend(unique_json)

    else:
        json_re = fda.fda_results(urls)
    
    return json_re

search = input("Query: ")
database = input(
    "choose database from (event, 510k, udi, recall, enforcement): ")

urls = fda.fda_url(search, data_base=database)
data = url_to_json(urls)

with open(f'FDA_JSON_{update_date}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)