import openFDA_url as fda
import pandas as pd

def url_to_df(url):
    json_re = fda.fda_results(url)
    df = pd.DataFrame (json_re)
    return df

def df_to_csv (urls):
    if isinstance(urls,list):
        final_df = pd.DataFrame()
        for url in urls:
            df = url_to_df(url)
            final_df = final_df.append(df)
        final_df.to_csv(f'general_search.csv')

    else:
        final_df = url_to_df(urls)
        final_df.to_csv(f'general_search.csv')


search = input("Query: ")
database = input ("choose database from (event, udi, recall, enforcement): ")

urls = fda.fda_url(search, data_base= database)
df_to_csv(urls)