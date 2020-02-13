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
    writer = csv.writer(file, delimiter=';')
    writer.writerow(['report_numbe', 'manufacturer_d_name','product_problem_flag', 'date_received',
                     'brand_name', 'device_name', 'product_problems', 'text'])

    for record in event_data:
        report_number = record['report_number']
        manufacturer_d_name = record['device'][0]['manufacturer_d_name']
        product_problem_flag = record['product_problem_flag']
        date_received = record['date_received']
        brand_name = record['device'][0]['brand_name']
        device_name = record['device'][0]['openfda']['device_name']

        try:
            product_problems = utils.stop_char(record['product_problems'])
        except KeyError:
            product_problems = []

        text = utils.stop_char(record['mdr_text']) 

        writer.writerow([report_number, manufacturer_d_name, product_problem_flag, date_received, brand_name, device_name, product_problems, text])


os.startfile('FDA_event.csv')