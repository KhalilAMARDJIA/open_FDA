
import pandas as pd
from collections import Counter
import plotly.express as px

data = pd.read_csv("event_data.csv", sep=";")
data = data.dropna()


fig = px.bar(
    template='simple_white',
    y='manufacturer_d_name',
    color='brand_name',
    color_discrete_sequence=px.colors.sequential.Cividis,
    data_frame=data,
    title=f'openFDA manufacturer and brand names from {len(data)} reports'
)
fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/Manufacturer & brand names.html", auto_open=True)


def str_pd_series_tolist(pd_series):
    main_list = []
    for item in pd_series:
        lst = item.strip('][').replace("'", "").split(', ')
        main_list += lst
    return main_list

# Patient problems analysis

patient_problems = str_pd_series_tolist(data['patient_problems'])
patient_problems_df = pd.DataFrame(
    dict(Counter(patient_problems)), index=['n'])
patient_problems_df = patient_problems_df.transpose().sort_values(by='n')

ftr_patient = ['No Code Available', 'No Known Impact Or Consequence To Patient', 'Symptoms or Conditions', 'No Information', 'No Consequences Or Impact To Patient',
            'Appropriate Clinical Signs', 'No Clinical Signs', 'Conditions Term / Code Not Available', 'Insufficient Information', 'No Patient Involvement', 'Reaction', 'Patient Problem/Medical Problem']

patient_problems_df = patient_problems_df.loc[~patient_problems_df.index.isin(
    ftr_patient)]
patient_problems_df = patient_problems_df.reset_index().rename(columns={'index': 'patient_problems'})
patient_problems_df = patient_problems_df.nlargest(20, columns='n')
fig = px.bar(
    template='simple_white',
    x = 'n',
    y='patient_problems',
    data_frame=patient_problems_df,
    title=f'openFDA patient problems from {len(data)} reports'
)
fig.update_traces(marker_line_color='black', marker_line_width=1, marker_color = 'lightgray')
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/Patient problems.html", auto_open=True)


# product problems analysis

product_problems = str_pd_series_tolist(data['product_problems'])
product_problems_df = pd.DataFrame(
    dict(Counter(product_problems)), index=['n'])
product_problems_df = product_problems_df.transpose().sort_values(by='n')


ftr_product = ['Adverse Event Without Identified Device or Use Problem',
            'Appropriate Term/Code Not Available', 'Unknown (for use when the device problem is not known)', 'Insufficient Information', 'No Apparent Adverse Event']

product_problems_df = product_problems_df.loc[~product_problems_df.index.isin(
    ftr_product)]

product_problems_df = product_problems_df.reset_index().rename(columns={'index': 'product_problems'})
product_problems_df = product_problems_df.nlargest(20, columns='n')

fig = px.bar(
    template='simple_white',
    x = 'n',
    y='product_problems',
    data_frame=product_problems_df,
    title=f'openFDA product problems from {len(data)} reports'
)
fig.update_traces(marker_line_color='black', marker_line_width=1, marker_color = 'lightgray')
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/Product problems.html", auto_open=True)
