
import pandas as pd
from collections import Counter
import plotly.express as px
import re
data = pd.read_csv("event_data.csv", sep="|")
data = data.dropna()


# Function that transform nested data into lists
def str_pd_series_tolist(pd_series):
    main_list = []
    for item in pd_series:
        lst = item.strip('][').replace("'", "").split(', ')
        main_list += lst
    return main_list


# Patient problems matrix
patient_problems_list = str_pd_series_tolist(data.patient_problems)
patient_problems_set = set(patient_problems_list)

patient_p_matrix = pd.DataFrame()

for patient_p in patient_problems_set:
    patient_p_matrix[patient_p] = data.patient_problems.str.count(
        patient_p, flags=re.IGNORECASE)

for col in patient_p_matrix.columns:
    patient_p_matrix.loc[patient_p_matrix[col] > 0, col] = 1

# Product problems matrix
product_problems_list = str_pd_series_tolist(data.product_problems)
product_problems_set = set(product_problems_list)

product_p_matrix = pd.DataFrame()

for product_p in product_problems_set:
    product_p_matrix[product_p] = data.product_problems.str.count(
        product_p, flags=re.IGNORECASE)

for col in product_p_matrix.columns:
    product_p_matrix.loc[product_p_matrix[col] > 0, col] = 1



pubmed_full = pd.concat([data, patient_p_matrix, product_p_matrix], axis=1, join='inner')

pubmed_full.to_csv('test.csv', sep= '|')