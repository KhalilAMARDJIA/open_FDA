def main():

   from general_openFDA import general_json
   import openFDA_parser
   import pandas as pd

   search = input("Query: ")
   search = search.replace(" ", "+AND+")


   database = input(
      "choose database from (event, 510k, udi, recall, enforcement, registrationlisting, classification): ")

   data, database = general_json(query = search, database = database)


   if database == 'event':
      df = openFDA_parser.parser_event(data= data)
   elif database == '510k':
      df = openFDA_parser.parser_510k(data= data)
   elif database == 'udi':
      df = openFDA_parser.parser_udi(data= data)
   elif database == 'recall':
      df = openFDA_parser.parser_recalls(data = data)
   else:
      print(f'the {database} is not supported by openFDA_parser')

   df = pd.DataFrame(df)

   csv_name = f'saved_csv/{database}_data.csv'
   df.to_csv(csv_name, sep= '|', encoding= 'UTF-8')

if __name__ == "__main__":
   main()