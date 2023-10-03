import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import openFDA_parser
import sys
import json
import math
import requests

def fetch_fda_data(query, database='event', count=False, field_count='', limit=1000, api_key='WuFW3nIY42Jq1SR9STTbDlQOfYNORGfeHsk5FFU9'):
    base_url = f'https://api.fda.gov/device/{database}.json?api_key={api_key}&search='

    try:
        if count:
            url = f'{base_url}{query}&count={field_count}'
        else:
            meta_url = f'{base_url}{query}'
            json_re = requests.get(meta_url).json()
            number_results = json_re['meta']['results']['total']

            if number_results == 0:
                st.warning("The search query returned 0 results. Please try a different query.")
                return None, None, None, 0  # Return zero results

            urls = [f'{base_url}{query}&limit={limit}&skip={1000 * i}' for i in range(math.ceil(number_results / 1000))] if number_results > 1000 else [f'{base_url}{query}&limit={limit}&skip=0']

            data = []
            for url in urls:
                response = requests.get(url)
                response.raise_for_status()  # Raise an error for non-OK responses
                unique_json = json.loads(response.text)['results']
                data.extend(unique_json)

            with open('openFDA_raw_data.json', 'w') as f:
                json.dump(data, f, indent=5)

            last_updated = json_re['meta']['last_updated']
            n_results = number_results

            return data, database, last_updated, n_results

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        return None, None, None, str(e)  # Return the error message as a string
    except KeyError:
        st.error("Error: Unexpected response format from openFDA API.Please try other keywords")
        return None, None, None, "None"

def search_data(query, database, from_date, to_date):
    data, database, last_updated, n_results = fetch_fda_data(query=query, database=database)
    
    parser_functions = {
        'event': openFDA_parser.parser_event,
        '510k': openFDA_parser.parser_510k,
        'udi': openFDA_parser.parser_udi,
        'recall': openFDA_parser.parser_recalls
    }
    
    df = pd.DataFrame(parser_functions.get(database, lambda data: [])(data))
    
    return df, database, last_updated, n_results

# Set Streamlit app title and layout
st.set_page_config(layout="wide")
col1, col2, col3 = st.columns([2, 2, 1])
st.title('Search openFDA Database')
st.sidebar.title('Settings')

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None

if 'plot_container' not in st.session_state:
    st.session_state.plot_container = None

# Add query input
query = st.sidebar.text_input('Query', '')
if not query:
    st.warning('Please enter a query.')
    st.stop()

# Add database selection
database = st.sidebar.selectbox('Database', ['event', '510k', 'udi', 'recall'])

# Add date range selection
from_date = st.sidebar.date_input('From Date (YYYY-MM-DD)', datetime.today() - timedelta(days=365.25 * 5))
to_date = st.sidebar.date_input('To Date (YYYY-MM-DD)', datetime.today())

# Add search button
search_button = st.sidebar.button('Search')

if search_button:
    # If date range is specified, add it to the search query
    if from_date and to_date:
        date_filter = f'+AND+[{from_date.strftime("%Y-%m-%d")}+TO+{to_date.strftime("%Y-%m-%d")}]'
        query += date_filter

    df, saved_database, last_updated, n_results = search_data(query, database, from_date, to_date)

    csv_path = f'saved_csv/{database}_data.csv'

    try:
        df.to_csv(csv_path, sep='|', encoding='UTF-8')
    except Exception as e:
        st.error(f"Error saving CSV file: {str(e)}")
        st.stop()  # Stop execution if there's an error

    col1.success(f"Search for openFDA in {saved_database} database is completed.")

    col3.metric(label="Number of Results", value=n_results)
    col3.metric(label="Last Updated", value=last_updated)

    col2.download_button(label="Download CSV", data=df.to_csv(index=False),  key='download_csv', file_name=f'{database}_data.csv', mime='text/csv')

    # Store the DataFrame in session state
    st.session_state.df = df

# Function to execute event_plot.py
def execute_event_plot():
    virtualenv_python = sys.executable  # Get the path to the currently running Python executable
    script_path = "Misc/event_plot.py"
    subprocess.run([virtualenv_python, script_path])

# Create a button to execute the script if the selected database is "event"
if database == 'event' and st.button("Execute event_plot.py"):
    execute_event_plot()
    st.success("event_plot.py executed successfully!")

# Display the main window
st.sidebar.write("[Go back to Search Page](#settings)")
