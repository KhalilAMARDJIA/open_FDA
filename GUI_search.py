import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import subprocess
from general_openFDA import general_json
import openFDA_parser
import sys


# Define the search_data function without caching
def search_data(query, database, from_date, to_date):
    data, database, last_updated, n_results = general_json(query=query, database=database)
    if database == 'event':
        df = openFDA_parser.parser_event(data=data)
    elif database == '510k':
        df = openFDA_parser.parser_510k(data=data)
    elif database == 'udi':
        df = openFDA_parser.parser_udi(data=data)
    elif database == 'recall':
        df = openFDA_parser.parser_recalls(data=data)    
    else:
        df = pd.DataFrame()  # Placeholder for other databases
    df = pd.DataFrame(df)
    return df, database, last_updated, n_results

# Set Streamlit app title and layout
st.set_page_config(layout="wide")
col1, col2, col3 = st.columns([2,2,1])
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

    csv_path = f'saved_csv/{database}_data.csv'

    try:
        df.to_csv(csv_path, sep='|', encoding='UTF-8')
    except Exception as e:
        st.error(f"Error saving CSV file: {str(e)}")

    col1.success(f"""
               Search for openFDA in {saved_database} database is completed.
               """)
    
    col3.metric(label= "Number of Results", value=n_results)
    col3.metric(label= "Last Updated", value=last_updated)

    col2.download_button(label="Download CSV", data=df.to_csv(index=False), key='download_csv')
    
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