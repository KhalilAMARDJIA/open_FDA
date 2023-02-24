# Import necessary modules
import sys
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton, QMessageBox
from general_openFDA import general_json  # custom module
import openFDA_parser  # custom module
import pandas as pd

# Define the main window class
class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle('Search Database')
        self.setGeometry(700, 50, 1000, 300)

        # Add query label and text box
        self.query_label = QLabel('Query', self)
        self.query_label.move(20, 20)
        self.query_text = QLineEdit(self)
        self.query_text.setPlaceholderText('')
        self.query_text.move(80, 20)
        self.query_text.resize(900, 22)

        # Add database label and combo box
        self.database_label = QLabel('Database', self)
        self.database_label.move(20, 50)
        self.database_combo = QComboBox(self)
        self.database_combo.addItems(['event', '510k', 'udi', 'recall'])
        self.database_combo.move(80, 50)
        self.database_combo.resize(260,22)

        # Add date labels and pickers
        self.from_date_label = QLabel('From Date (YYYY-MM-DD)', self)
        self.from_date_label.move(20, 80)
        self.from_date_picker = QDateEdit(self)
        self.from_date_picker.setDisplayFormat('yyyy-MM-dd')
        self.from_date_picker.move(200, 80)
        self.to_date_label = QLabel('To Date (YYYY-MM-DD)', self)
        self.to_date_label.move(20, 110)
        self.to_date_picker = QDateEdit(self)
        self.to_date_picker.setDisplayFormat('yyyy-MM-dd')
        self.to_date_picker.move(200, 110)
        self.to_date_picker.setDate(QDate.currentDate())  # set the default date to the current date

        # Add search button
        self.search_button = QPushButton('Search', self)
        self.search_button.clicked.connect(self.search)
        self.search_button.move(100, 150)

        # Show the window
        self.show()

    def search(self):
        # Get user inputs from the GUI
        query = self.query_text.text()
        search = query.replace(" ", "+AND+")
        database = self.database_combo.currentText()
        from_date = self.from_date_picker.date().toString(Qt.ISODate)
        to_date = self.to_date_picker.date().toString(Qt.ISODate)

        # If date range is specified, add it to the search query
        if from_date and to_date:
            date_filter = f'+AND+date_received:[{from_date}+TO+{to_date}]'
            search += date_filter

        # Get the parser function for the selected database
        parser_functions = {
            'event': openFDA_parser.parser_event,
            '510k': openFDA_parser.parser_510k,
            'udi': openFDA_parser.parser_udi,
            'recall': openFDA_parser.parser_recalls,
        }
        parser_func = parser_functions.get(database)

        if parser_func is None:
            QMessageBox.critical(self, "Error", f"The {database} database is not supported by openFDA_parser")
            return

        data, database = general_json(query=search, database=database)
        df = parser_func(data=data)
        df = pd.DataFrame(df)

        csv_name = f'saved_csv/{database}_data.csv'
        df.to_csv(csv_name, sep='|', encoding='UTF-8')

        QMessageBox.information(self, "Search Completed", f"Search for openFDA '{query}' in {database} database is completed.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
