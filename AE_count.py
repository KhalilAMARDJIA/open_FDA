import json
import pandas as pd
import re
import plotly.express as px
    
# fetch data from PubMed
pubmed_raw_data = pd.read_csv('event_data.csv', sep = "|")

# open complications database
with open('./databases/complications_db.json') as file:
    complications_db = json.load(file)

# check if complications are present in the texts

main_cat = []
complications = []
complications_matrix = pd.DataFrame()

for complication in complications_db['complications']:
    for AE in complications_db['complications'][complication]:
        main_cat.append(complication)
        complications.append(AE)
        for syn in complications_db['complications'][complication][AE]:
            search_or_syno = '|'.join(
                complications_db['complications'][complication][AE])
            try:
                search_or_syno = search_or_syno.replace("(", "\(")
                search_or_syno = search_or_syno.replace(")", "\)")

                complications_matrix[AE] = pubmed_raw_data.text.str.count(
                    search_or_syno, flags=re.IGNORECASE)
            except:
                pass

for col in complications_matrix.columns:
    complications_matrix.loc[complications_matrix[col] > 0, col] = 1

# before transpose joint final output csv

complications_matrix.to_csv('./saved_csv/matrix_complications.csv', sep=';')

# ploting

complication_matrix = complications_matrix.transpose()

body_map = dict(zip(complications, main_cat))  # create map from 2 list as dict

complication_matrix_plot = complication_matrix.sum(axis=1).reset_index()
complication_matrix_plot['main_cat'] = complication_matrix_plot['index'].map(body_map)
complication_matrix_plot = complication_matrix_plot.rename(
    columns={'index': 'complication', 0: 'n'})
complication_matrix_plot = complication_matrix_plot.sort_values([
                                                                'main_cat', 'n'])
complication_matrix_plot = complication_matrix_plot[complication_matrix_plot.n > 0]

fig = px.bar(
    data_frame=complication_matrix_plot,
    template='simple_white',
    x='n',
    y='complication',
    color='main_cat',
    color_discrete_sequence=px.colors.diverging.curl,
    title= f'PubMed data extracted from {len(pubmed_raw_data)} texts'
)


fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(font_family="JetBrainsMono NF")

fig.write_html("./plots/complications.html", auto_open=True)



t_complication_matrix = complication_matrix.transpose()

event_full = pd.concat([pubmed_raw_data, t_complication_matrix], axis=1, join="inner")
event_full = pubmed_full[pubmed_full.columns.drop(list(pubmed_full.filter(regex='Unnamed')))]
event_full.to_csv("./saved_csv/event_full.csv", sep = ";")

