import csv
import json
from openFDA_url import fda_results
from openFDA_url import fda_url


def UDI_parser(result):
    try:
        company_name = result['company_name']
        k_number = result['premarket_submissions'][0]['submission_number']
        is_single_use = result['is_single_use']
        brand_name = result['brand_name']
        device_sizes = result['device_sizes']
        writer.writerow([company_name, k_number, is_single_use, brand_name, device_sizes])
    except KeyError:
        print("skiped record for missing value")


search = input("search_UDI_database: ")
urls = fda_url(search)
with open ('UDI_data.csv', 'w', newline='') as f:
    writer = csv.writer(f,delimiter="\t")
    writer.writerow(["company_name","k_number", "is_single_use",  "brand_name", "device_sizes"])

    if isinstance(urls,list):
        for url in urls:
            results = fda_results(url)
            for result in results :
                UDI_parser(result)

    else:
        results = fda_results(urls)
        for result in results :
            UDI_parser(result)

