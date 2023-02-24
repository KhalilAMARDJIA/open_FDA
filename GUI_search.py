import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = 'Search Database'
        self.left = 700
        self.top = 50
        self.width = 1000
        self.height = 300

        self.UI()

    def UI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.label1 = QLabel('Query', self)
        self.label1.move(20, 20)

        self.text1 = QLineEdit(self)
        self.text1.setPlaceholderText('')
        self.text1.move(80, 20)
        self.text1.resize(900, 22)

        self.label2 = QLabel('Database', self)
        self.label2.move(20, 50)

        dblist = ['event', '510k', 'udi', 'recall', 'enforcement', 'registrationlisting', 'classification']

        self.combo1 = QComboBox(self)
        self.combo1.addItems(dblist)
        self.combo1.move(80, 50)
        self.combo1.resize(260,22)

        self.label3 = QLabel('From Date (YYYY-MM-DD)', self)
        self.label3.move(20, 80)

        self.date1 = QDateEdit(self)
        self.date1.setDisplayFormat('yyyy-MM-dd')
        self.date1.move(200, 80)

        self.label4 = QLabel('To Date (YYYY-MM-DD)', self)
        self.label4.move(20, 110)

        self.date2 = QDateEdit(self)
        self.date2.setDisplayFormat('yyyy-MM-dd')
        self.date2.move(200, 110)

        self.button1 = QPushButton('Search', self)
        self.button1.clicked.connect(self.main)
        self.button1.move(100, 150)
        
        self.show()


    def main(self):
        query = self.text1.text()
        search = query.replace(" ", "+AND+")
        database = self.combo1.currentText()
        from_date = self.date1.date().toString('yyyy-MM-dd')
        to_date = self.date2.date().toString('yyyy-MM-dd')

        if from_date and to_date:
            date_filter = f'+AND+date_received:[{from_date}+TO+{to_date}]'
            search += date_filter

        from general_openFDA import general_json
        import openFDA_parser
        import pandas as pd

        data, database = general_json(query=search, database=database)

        if database == 'event':
            df = openFDA_parser.parser_event(data=data)
        elif database == '510k':
            df = openFDA_parser.parser_510k(data=data)
        elif database == 'udi':
            df = openFDA_parser.parser_udi(data=data)
        elif database == 'recall':
            df = openFDA_parser.parser_recalls(data=data)
        else:
            print(f'the {database} is not supported by openFDA_parser')

        df = pd.DataFrame(df)

        csv_name = f'saved_csv/{database}_data.csv'
        df.to_csv(csv_name, sep='|', encoding='UTF-8')

        # show message box
        QMessageBox.information(self, "Search Completed", f"Search for '{query}' in {database} database is completed.")


App = QApplication(sys.argv)
Window = Window()
sys.exit(App.exec())
