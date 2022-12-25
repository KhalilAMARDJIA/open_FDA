
import pandas as pd

import plotly.express as px

data = pd.read_csv("saved_csv/recall_data.csv", sep="|")


fig = px.bar(
    template='simple_white',
    x='device_name',
    color='recalling_firm',
    color_discrete_sequence=px.colors.sequential.Cividis,
    data_frame=data,
    title=f'openFDA recalling firm and device names from {len(data)} reports'
)

fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/recalled devices.html", auto_open=True)


fig = px.bar(
    template='simple_white',
    x = 'device_name',
    color= 'root_cause_description',
    color_discrete_sequence=px.colors.sequential.Cividis,
    data_frame=data,
    title=f'openFDA patient problems from {len(data)} reports'
)
fig.update_traces(marker_line_color='black', marker_line_width=1)
fig.update_layout(font_family="Courier New")
fig.write_html("./plots/recall root cause.html", auto_open=True)
