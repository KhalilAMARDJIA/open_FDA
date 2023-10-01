import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from general_openFDA import general_json
import openFDA_parser

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
        st.success("CSV file saved successfully.")
    except Exception as e:
        st.error(f"Error saving CSV file: {str(e)}")

    st.success(f"""
               Search for openFDA in {saved_database} database is completed.
               
               Last Updated: {last_updated}

               Number of Results: {n_results}

               """)
    st.download_button(label="Download CSV", data=df.to_csv(index=False), key='download_csv')
    
    # Store the DataFrame in session state
    st.session_state.df = df


# Display the main window
st.sidebar.write("[Go back to Search Page](#settings)")


if st.session_state.df is not None:
    st.subheader("Select Columns for Plotting")

    # Determine available columns based on the selected database
    if database == 'event':
        available_columns = st.session_state.df.columns
    elif database == '510k':
        available_columns = st.session_state.df.columns
    elif database == 'udi':
        available_columns = st.session_state.df.columns
    elif database == 'recall':
        available_columns = st.session_state.df.columns
    else:
        available_columns = []  # No columns available for other databases
    
    x_column = st.selectbox('X-axis', available_columns)
    y_column = st.selectbox('Y-axis', available_columns)

    st.subheader("Sample Plot")

    # Check if both x_column and y_column are selected
    if x_column and y_column:

        # Create a new plot container and remove the old one
        if st.session_state.plot_container:
            st.session_state.plot_container.empty()
        
        # Create the plot using the data from session state
        fig = px.bar(st.session_state.df, x=x_column, y=y_column, title=f'{x_column} vs {y_column}')
        st.session_state.plot_container = st.empty()
        st.session_state.plot_container.plotly_chart(fig)

    else:
        st.warning("Plotting is not available for the selected database.")
