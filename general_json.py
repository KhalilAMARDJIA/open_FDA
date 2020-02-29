import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import openFDA_url as fda
import json

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
search = search.replace(" ", "+AND+")
search = "("+ search + ")"
update_date = fda.get_meta(f'https://api.fda.gov/device/event.json?search={search}')['last_updated']

database = input(
    "choose database from (event, 510k, udi, recall, enforcement, registrationlisting, classification): ")

urls = fda.fda_url(search, data_base=database)
data = url_to_json(urls)

with open(f'{update_date}_FDA_JSON_{database}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
