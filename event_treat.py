import pandas as pd
import plotly.express as px
import re

data = pd.read_csv("event_data.csv", sep="|", index_col=0)
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
    patient_p_matrix[patient_p] = data.patient_problems.str.count(patient_p, flags=re.IGNORECASE)

for col in patient_p_matrix.columns:
    patient_p_matrix.loc[patient_p_matrix[col] > 0, col] = 1

# Product problems matrix
product_problems_list = str_pd_series_tolist(data.product_problems)
product_problems_set = set(product_problems_list)



product_p_matrix = pd.DataFrame()

for product_p in product_problems_set:
    product_p_matrix[product_p] = data.product_problems.str.count(product_p, flags=re.IGNORECASE)

for col in product_p_matrix.columns:
    product_p_matrix.loc[product_p_matrix[col] > 0, col] = 1



pubmed_full = pd.concat([data, patient_p_matrix, product_p_matrix], axis=1, join='inner')

pubmed_full_pivot = pd.melt(pubmed_full, value_vars=pubmed_full.columns[8:len(pubmed_full.columns)+1], id_vars=pubmed_full.columns[0:8])

filter = pubmed_full_pivot['value'] > 0

pubmed_full_pivot = pubmed_full_pivot[filter]

pubmed_full_pivot.pivot_table()

plot_1 = pubmed_full_pivot.groupby(['variable', 'manufacturer_d_name']).agg({'value': 'sum'}).reset_index()

event_type = []
for event in plot_1.variable:
    if event in patient_problems_set:
        event_type.append('Patient problem')
    else:
        event_type.append('Product problem')
plot_1['event_type'] = event_type
plot_1 = plot_1.sort_values(by = ['value', 'event_type'], ascending = [False, False], na_position = 'first')


fig = px.bar(
    template='simple_white',
    x='value',
    y='variable',
    color='event_type',
    color_discrete_sequence=px.colors.sequential.Cividis,
    data_frame=plot_1,
    title=f'openFDA reports'
)
fig['layout']['yaxis']['autorange'] = "reversed"
fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/test.html", auto_open=True)
