import os
os.chdir('I:\openFDA\openFDA_functions')
from general_openFDA import general_json
import openFDA_parser
import pandas as pd

data, data_base = general_json(query = "In2Bones", data_base = "udi")


if data_base == 'event':
   df = openFDA_parser.parser_event(data= data)
elif data_base == '510k':
   df = openFDA_parser.parser_510k(data= data)
elif data_base == 'udi':
   df = openFDA_parser.parser_udi(data= data)
else:
   print(f'the {data_base} is not supported by openFDA_parser')


df = pd.DataFrame(df)
df.to_csv(f'{data_base}_data.csv', sep= ';', encoding= 'UTF-8')