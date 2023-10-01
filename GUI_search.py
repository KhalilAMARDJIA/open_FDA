import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from general_openFDA import general_json
import openFDA_parser

# Define the search_data function without caching
def search_data(query, database, from_date, to_date):
    data, database, last_updated, n_results = general_json(query=query, database=database)
    df = openFDA_parser.parser_event(data=data)
    df = pd.DataFrame(df)
    return df, database, last_updated, n_results

# Set Streamlit app title and layout
st.set_page_config(layout="wide")
st.title('Search openFDA Database')
st.sidebar.title('Settings')

# Add query input
query = st.sidebar.text_input('Query', '')
if not query:
    st.warning('Please enter a query.')
    st.stop()

# Add database selection
database = st.sidebar.selectbox('Database', ['event', '510k', 'udi', 'recall'])

# Add date range selection
from_date = st.sidebar.date_input('From Date (YYYY-MM-DD)', datetime.today() - timedelta(days=365.25*5))
to_date = st.sidebar.date_input('To Date (YYYY-MM-DD)', datetime.today())

# Add search button
search_button = st.sidebar.button('Search')

if search_button:
    # If date range is specified, add it to the search query
    if from_date and to_date:
        date_filter = f'+AND+[{from_date.strftime("%Y-%m-%d")}+TO+{to_date.strftime("%Y-%m-%d")}]'
        query += date_filter

    df, saved_database, last_updated, n_results = search_data(query, database, from_date, to_date)

    st.success(f"Search for openFDA '{query}' in {saved_database} database is completed.")
    st.write(f"Last Updated: {last_updated}")
    st.write(f"Number of Results: {n_results}")
    st.download_button(label="Download CSV", data=df.to_csv(index=False), key='download_csv')

# Display the main window
st.sidebar.write("[Go back to Search Page](#settings)")
st.write("## Main Window")
st.write("This is the main content area where you can display information or results.")
