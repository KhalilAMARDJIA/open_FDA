import json
from datetime import datetime
from pathlib import Path

def main():
    from general_openFDA import general_json
    import openFDA_parser
    import pandas as pd

    print("\n" + "="*60)
    print("OpenFDA SEARCH")
    print("="*60 + "\n")

    # Get search query
    search = input("Query: ")
    original_query = search  # Store original for metadata
    search = search.replace(" ", "+AND+")

    # Get database selection
    database = input(
        "Choose database from (event, 510k, udi, recall, enforcement, registrationlisting, classification): ")

    print("\n" + "-"*60)
    print("EXECUTING SEARCH...")
    print("-"*60 + "\n")

    # Execute search
    data, database, last_updated, n_results = general_json(query=search, database=database)

    # Print search results summary
    print(f"✓ Search completed successfully!")
    print(f"  • Database: {database}")
    print(f"  • Query: {original_query}")
    print(f"  • Number of results: {n_results:,}")
    print(f"  • Last updated: {last_updated}")
    print(f"  • Records retrieved: {len(data):,}")
    print()

    # Parse data based on database type
    if database == 'event':
        df = openFDA_parser.parser_event(data=data)
    elif database == '510k':
        df = openFDA_parser.parser_510k(data=data)
    elif database == 'udi':
        df = openFDA_parser.parser_udi(data=data)
    elif database == 'recall':
        df = openFDA_parser.parser_recalls(data=data)
    else:
        print(f'⚠ Warning: The {database} database is not supported by openFDA_parser')
        print("  Data will be saved as JSON only, no CSV will be generated.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(df)

    # Prepare metadata
    metadata = {
        "query": {
            "original_query": original_query,
            "formatted_query": search,
            "database": database
        },
        "results": {
            "total_results": n_results,
            "records_retrieved": len(data),
            "records_parsed": len(df)
        },
        "timestamp": {
            "search_executed": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_last_updated": last_updated
        },
        "api": {
            "source": "OpenFDA",
            "endpoint": f"https://api.fda.gov/device/{database}.json"
        }
    }

    # Create saved_csv directory if it doesn't exist
    Path("saved_csv").mkdir(exist_ok=True)

    # Save CSV
    csv_name = f'saved_csv/{database}_data.csv'
    df.to_csv(csv_name, sep='|', encoding='UTF-8', index=False)
    print(f"✓ Data saved to: {csv_name}")

    # Save metadata
    metadata_name = f'saved_csv/{database}_metadata.json'
    with open(metadata_name, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
    print(f"✓ Metadata saved to: {metadata_name}")

    print("\n" + "="*60)
    print("SEARCH SUMMARY")
    print("="*60)
    print(f"Query:        {original_query}")
    print(f"Database:     {database}")
    print(f"Results:      {n_results:,} records")
    print(f"Last Updated: {last_updated}")
    print(f"CSV File:     {csv_name}")
    print(f"Metadata:     {metadata_name}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()