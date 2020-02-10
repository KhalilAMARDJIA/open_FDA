import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import openFDA_url as fda
import pandas as pd

update_date = fda.get_meta('https://api.fda.gov/device/event.json?search=in2bones')['last_updated']

def url_to_df(url):
    json_re = fda.fda_results(url)
    df = pd.DataFrame(json_re)
    return df

def df_to_csv(urls):
    
    if isinstance(urls, list):
        final_df = pd.DataFrame()
        for url in urls:
            df = url_to_df(url)
            final_df = final_df.append(df, sort = False)
        final_df.to_csv(f'FDA_CSV_{update_date}.csv', encoding='utf-8-sig', sep=";")

    else:
        final_df = url_to_df(urls)
        final_df.to_csv(f'FDA_CSV_{update_date}.csv', encoding='utf-8-sig', sep=";")


search = input("Query: ")
database = input(
    "choose database from (event, 510k, udi, recall, enforcement): ")

urls = fda.fda_url(search, data_base=database)
df_to_csv(urls)

os.startfile(f'FDA_CSV_{update_date}.csv')
