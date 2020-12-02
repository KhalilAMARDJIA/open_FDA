import json
import csv
import os
import openfda_utils as utils

ext = '.json'
db_file = 'FDA_JSON_event'

filename = utils.relevant_file(db_file, ext)

with open(filename, encoding='utf8') as file:
  event_data = json.load(file)


with open('FDA_event.csv', 'w', newline='', encoding='utf8') as file:
    writer = csv.writer(file, delimiter='|')
    writer.writerow(['report_numbe', 'manufacturer_d_name','product_problem_flag', 'date_received',
                     'brand_name', 'product_problems', 'text'])

    for record in event_data:
        report_number = record['report_number']
        manufacturer_d_name = record['device'][0]['manufacturer_d_name']
        product_problem_flag = record['product_problem_flag']
        date_received = record['date_received']
        brand_name = record['device'][0]['brand_name']

        try:
            product_problems = record['product_problems']
        except KeyError:
            product_problems = ""

        try:
            text_1_code = record['mdr_text'][1]['text_type_code']

        except IndexError:
            text_1_code = ""
        
        except KeyError:
            text_1_code = ""
        
        try:
            text_1 = record['mdr_text'][1]['text'].lower()

        except IndexError:
            text_1 = ""

        except KeyError:
            text_1 = ""

        try:
            text_0_code = record['mdr_text'][0]['text_type_code']

        except KeyError:
            text_0_code = ""
        try:
            text_0 = record['mdr_text'][0]['text'].lower()

        except KeyError:
            text_0 = ""
        

        text =  f"{text_1_code}: {text_1} {text_0_code}: {text_0}"
        





        writer.writerow([report_number,manufacturer_d_name, product_problem_flag, date_received, brand_name, product_problems, text])
