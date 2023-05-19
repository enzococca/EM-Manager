import splash
from PyQt5.QtCore import (QAbstractTableModel,QVariant,
                          Qt)
from PyQt5.QtWidgets import (QDialog,
                             QFileDialog,
                             QAction,
                             QTableWidgetItem,

                             QMainWindow,
                             QApplication,

                             QPushButton,
                             QHBoxLayout,
                             QVBoxLayout,
                             QInputDialog,
                             QComboBox)
from PyQt5.uic import loadUiType
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_directory)

from interactive_matrix import *
import json
import platform
import csv
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
import io
from d_graphml import GraphWindow
from check_graphviz_path import check_graphviz
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from config import config

MAIN_DIALOG_CLASS, _ = loadUiType(
    os.path.join(os.path.dirname(__file__),  'ui', 'edm2grapml.ui'))

class EpochDialog(QDialog):
    def __init__(self, epochs_df, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Seleziona epoca storica")
        self.setWindowModality(Qt.ApplicationModal)

        # Create the epoch combobox
        self.combo_box = QComboBox()
        for _, row in epochs_df.iterrows():
            epoch = row["Periodo"]
            evento= row["Evento"]
            combo_item = f"{epoch} - {evento}"
            self.combo_box.addItem(combo_item)

        # Create the OK and Cancel buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Annulla")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Add the combobox and buttons to the dialog layout
        layout = QVBoxLayout()
        layout.addWidget(self.combo_box)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        # Aggiungi questo nel tuo metodo __init__ o dove preferisci




    def get_selected_epoch(self):
        if self.exec_() == QDialog.Accepted:
            selected_epoch = self.combo_box.currentText()
            return selected_epoch
        return None
class UnitDialog(QDialog):
    def __init__(self, unit_df, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Seleziona unità tipo")
        self.setWindowModality(Qt.ApplicationModal)

        # Create the epoch combobox
        self.combo_box = QComboBox()
        for _, row in unit_df.iterrows():
            tipo = row["TIPO"]
            simbolo= row["Simbolo"]
            combo_item = f"{tipo} - {simbolo}"
            self.combo_box.addItem(combo_item)

        # Create the OK and Cancel buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Annulla")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Add the combobox and buttons to the dialog layout
        layout = QVBoxLayout()
        layout.addWidget(self.combo_box)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        # Aggiungi questo nel tuo metodo __init__ o dove preferisci




    def get_selected_unit(self):
        if self.exec_() == QDialog.Accepted:
            selected_units = self.combo_box.currentText()
            selected_unit = selected_units.split('-')[0].strip()
            return selected_unit
        return None
class CSVMapper(QMainWindow, MAIN_DIALOG_CLASS):
    GRAPHML_PATH = None
    def __init__(self, parent=None,data_file=None, spreadsheet=None):

        super(CSVMapper, self).__init__(parent=parent)
        self.setupUi(self)
        self.custumize_gui()


        self.data_file = data_file
        self.spreadsheet = spreadsheet
        if data_file is not None:
            self.data_source = 'csv'
        elif spreadsheet is not None:
            self.data_source = 'google_sheet'
        else:
            self.data_source = None
        # Collegare i bottoni alle funzioni corrispondenti
        self.save_button.clicked.connect(self.save_csv)
        self.save_google_button.clicked.connect(self.save_google)
        self.update_button.clicked.connect(self.update_csv)
        self.rollback_button.clicked.connect(self.rollback_csv)
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.data_table.customContextMenuRequested.connect(self.show_epoch_dialog)
        self.data_table.customContextMenuRequested.connect(self.show_unit_dialog)
        self.save_google_button.setHidden(True)
        self.save_button.setHidden(True)
        self.statusbar.setSizeGripEnabled(False)

        self.statusbar.setStyleSheet("QStatusBar{border-top: 1px solid grey;}")
        check_graphviz(self.statusbar)
        # Crea un nuovo QWebEngineView
        self.help_view = QWebEngineView()
        # Imposta le dimensioni della finestra
        self.help_view.resize(800, 600)
        # Imposta il titolo della finestra
        self.help_view.setWindowTitle('Help')

        # Carica il file HTML
        self.help_view.load(QUrl.fromLocalFile(os.path.abspath('build/html/help.html')))

        # Crea l'azione Help
        self.help_action = QAction('Help', self)
        # Collega il segnale triggered dell'azione alla funzione show_help
        self.help_action.triggered.connect(self.show_help)
        # Aggiungi l'azione al menu
        self.menu_help_2.addAction(self.help_action)


    def show_help(self):
        self.help_view.show()
    def custumize_gui(self):
        """
        In the cutumize_gui() method, it is setting the window title, setting the geometry,
        and opening files for the template and data CSVs.
        """
        # Add the button to load data from a Google Sheet to the menubar

        google_sheet_action = QAction("Carica dati da un Google Sheet", self)
        google_sheet_action.triggered.connect(self.on_google_sheet_action_triggered)

        self.update_relationships_button.triggered.connect(self.update_relations)
        self.actionAggiorna_rapporti_Google.triggered.connect(self.update_relations_google)
        self.actionVisualizzatore_3D.triggered.connect(self.d_graph)

        def handle_check_relations_action():
            # Converti i dati della tabella in una lista di righe
            rows = []
            for i in range(self.data_table.rowCount()):
                row = []
                for j in range(self.data_table.columnCount()):
                    item = self.data_table.item(i, j)
                    row.append(item.text() if item else 'nan')
                rows.append(row)

            # Ottiengo l'header dalla tabella
            header = [self.data_table.horizontalHeaderItem(i).text() for i in range(self.data_table.columnCount())]

            # Controllo le relazioni e stampa gli errori nel QTextEdit
            errors = self.check_relations(rows, header)

            self.print_errors_to_textedit(errors, self.textEdit)

        self.Check_Error.triggered.connect(handle_check_relations_action)

        self.setCentralWidget(self.widget)

        self.statusbar.setSizeGripEnabled(False)

        self.statusbar.setStyleSheet("QStatusBar{border-top: 1px solid grey;}")
        self.actionCrea_progetto.triggered.connect(self.create_empty_csv)

        self.newProj.triggered.connect(self.create_empty_csv)

        self.openRecentProj.triggered.connect(self.open_recent_project)
        self.actionApri_progetto.triggered.connect(self.open_project)

    def open_project(self):
        projects_file = 'projects.json'

        # Fornisco un dialogo di selezione del file
        project, _ = QFileDialog.getOpenFileName(self, "Seleziona un progetto", "", "CSV Files (*.csv)")

        if project:  # Se un file è stato selezionato
            print(f"Apertura del progetto {project}")

            # Aggiungo il progetto alla lista dei progetti recenti
            if os.path.isfile(projects_file):
                with open(projects_file, 'r') as file:
                    projects = json.load(file)
            else:
                projects = []

            # Se il progetto non è già nella lista, aggiungilo
            if project not in projects:
                projects.append(project)

                # Salva la lista aggiornata nel file JSON
                with open(projects_file, 'w') as file:
                    json.dump(projects, file)

            # nome del progetto
            base_name = os.path.basename(project)
            base_name_no_ext = os.path.splitext(base_name)[0]  # Rimuovi l'estensione del file

            # Costruisco il percorso al file CSV
            csv_path = os.path.join(os.path.dirname(project), f"{base_name_no_ext}.csv")

            if os.path.isfile(csv_path):
                #Apro il file csv
                self.data_file = csv_path

                try:
                    self.transform_data(self.data_file, self.data_file)
                except AssertionError:
                    pass
                self.df = pd.read_csv(self.data_file, dtype=str)
                self.data_fields = self.df.columns.tolist()

                self.data_table.setDragEnabled(True)
                # Impostare il numero di righe e colonne nel QTableWidget
                self.data_table.setRowCount(len(self.df))
                self.data_table.setColumnCount(len(self.df.columns))

                # Impostare le etichette delle colonne orizzontali
                self.data_table.setHorizontalHeaderLabels(self.df.columns)

                # Inserire i dati nelle celle del QTableWidget
                for row in range(len(self.df)):
                    for col in range(len(self.df.columns)):
                        item = QTableWidgetItem(str(self.df.iat[row, col]))
                        self.data_table.setItem(row, col, item)
                for i in range(self.data_table.rowCount()):
                    self.data_table.setRowHeight(i, 50)

                for i in range(self.data_table.columnCount()):
                    self.data_table.setColumnWidth(i, 250)
            else:
                QMessageBox.warning(self,'Attenzione',f"Il file CSV {csv_path} non esiste")

    def open_recent_project(self):
        projects_file = 'projects.json'

        if os.path.isfile(projects_file):
            with open(projects_file, 'r') as file:
                projects = json.load(file)

            project, ok = QInputDialog.getItem(self, "Seleziona un progetto recente", "Progetti:", projects, 0, False)
            if ok and project:
                # qui puoi implementare il codice per aprire il progetto selezionato
                print(f"Apertura del progetto {project}")

                # Get the base name of the project
                base_name = os.path.basename(project)
                base_name_no_ext = os.path.splitext(base_name)[0]  # Rimuovi l'estensione del file

                # Costruisci il percorso al file CSV
                csv_path = os.path.join(project, f"{base_name_no_ext}.csv")

                if os.path.isfile(csv_path):
                    # Open the data CSV file
                    self.data_file = csv_path

                    try:
                        self.transform_data(self.data_file, self.data_file)
                    except AssertionError:
                        pass
                    self.df = pd.read_csv(self.data_file, dtype=str)
                    self.data_fields = self.df.columns.tolist()

                    self.data_table.setDragEnabled(True)
                    # Impostare il numero di righe e colonne nel QTableWidget
                    self.data_table.setRowCount(len(self.df))
                    self.data_table.setColumnCount(len(self.df.columns))

                    # Impostare le etichette delle colonne orizzontali
                    self.data_table.setHorizontalHeaderLabels(self.df.columns)

                    # Inserire i dati nelle celle del QTableWidget
                    for row in range(len(self.df)):
                        for col in range(len(self.df.columns)):
                            item = QTableWidgetItem(str(self.df.iat[row, col]))
                            self.data_table.setItem(row, col, item)
                    for i in range(self.data_table.rowCount()):
                        self.data_table.setRowHeight(i, 50)

                    for i in range(self.data_table.columnCount()):
                        self.data_table.setColumnWidth(i, 250)
                else:
                    QMessageBox.warning(self,'Attenzione',f"Il file CSV {csv_path} non esiste")


    def save_project_to_json(self, project_dir):
        projects_file = 'projects.json'
        projects = []

        if os.path.isfile(projects_file):
            with open(projects_file, 'r') as file:
                projects = json.load(file)

        projects.insert(0, project_dir)
        projects = projects[:5]

        with open(projects_file, 'w') as file:
            json.dump(projects, file)

    def create_empty_csv(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Seleziona la cartella e il nome del file', '',
                                               'CSV Files (*.csv)')

        if fname:
            # Crea le directory
            dir_name = os.path.dirname(fname)
            base_name = os.path.basename(fname)
            base_name_no_ext = os.path.splitext(base_name)[0]  # Rimuovi l'estensione del file

            dir_path = os.path.join(dir_name, base_name_no_ext)
            os.makedirs(dir_path, exist_ok=True)
            os.makedirs(os.path.join(dir_path, "DosCo"), exist_ok=True)
            os.makedirs(os.path.join(dir_path, "3d_obj"), exist_ok=True)

            # Crea il file CSV
            csv_path = os.path.join(dir_path, base_name)
            with open(csv_path, 'w',newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['nome us', 'tipo', 'tipo di nodi', 'descrizione', 'epoca',
                                 'epoca index', 'area', 'anteriore', 'posteriore', 'contemporaneo',
                                 'properties_ant', 'properties_post'])

            # Salva i dettagli del progetto
            self.save_project_to_json(dir_path)

        # Open the data CSV file
        self.data_file = csv_path

        try:
            self.transform_data(self.data_file, self.data_file)
        except AssertionError:
            pass
        self.df = pd.read_csv(self.data_file, dtype=str)
        self.data_fields = self.df.columns.tolist()

        self.data_table.setDragEnabled(True)
        # Impostare il numero di righe e colonne nel QTableWidget
        self.data_table.setRowCount(len(self.df))
        self.data_table.setColumnCount(len(self.df.columns))

        # Impostare le etichette delle colonne orizzontali
        self.data_table.setHorizontalHeaderLabels(self.df.columns)

        # Inserire i dati nelle celle del QTableWidget
        for row in range(len(self.df)):
            for col in range(len(self.df.columns)):
                item = QTableWidgetItem(str(self.df.iat[row, col]))
                self.data_table.setItem(row, col, item)
        for i in range(self.data_table.rowCount()):
            self.data_table.setRowHeight(i, 50)

        for i in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(i, 250)

    def d_graph(self):
        #richaimo il visualizzatore 3D
        #GraphWindow()
        GraphWindow(CSVMapper.GRAPHML_PATH)



    #serie di funzioni per cercare gli errori nelle relazioni
    # cerca duplicati nella stessa riga
    # cerca se le relazioni esistono
    # se le relazioni inverse esistono
    # il tipo di relazione se è corretto
    def check_duplicates(self, rows, header):
        errors = []
        for row in rows:
            for relation_type in ['anteriore', 'posteriore', 'properties_ant', 'properties_post']:
                if relation_type in header:
                    related_us_names = row[header.index(relation_type)]
                    if related_us_names != 'nan':
                        related_us_names = related_us_names.split(',')
                        if len(related_us_names) != len(set(related_us_names)):
                            errors.append((related_us_names), f"{related_us_names} is dupliacted")
        return errors
    def check_relation_exists(self,rows, header):
        errors = []
        for row in rows:
            us_name = row[0]
            for relation_type in ['anteriore', 'posteriore', 'properties_ant', 'properties_post']:
                related_us_names = row[header.index(relation_type)]
                if related_us_names != 'nan':
                    for related_us_name in related_us_names.split(','):
                        related_us_name = related_us_name.strip()
                        if not any(related_us_name in related_row for related_row in rows):
                            errors.append((us_name, related_us_name,
                                           f"{us_name} has a relation to {related_us_name} but {related_us_name} does not exist."))
        return errors
    def check_inverse_relation_exists(self,rows, header):
        errors = []
        for row in rows:
            us_name = row[0]
            for relation_type, inverse_relation_type in [('anteriore', 'posteriore'), ('posteriore', 'anteriore'),
                                                         ('properties_ant', 'properties_post'),
                                                         ('properties_post', 'properties_ant')]:
                related_us_names = row[header.index(relation_type)]
                if related_us_names != 'nan':
                    for related_us_name in related_us_names.split(','):
                        related_us_name = related_us_name.strip()
                        if not any(
                                us_name in related_row[header.index(inverse_relation_type)].split(',') for related_row
                                in rows if related_row[0] == related_us_name):
                            errors.append((us_name, related_us_name,
                                           f"{us_name} has a {relation_type} relation to {related_us_name} but {related_us_name} does not have a {inverse_relation_type} relation to {us_name}."))
        return errors
    def check_relation_type(self,rows, header):
        errors = []
        for row in rows:
            us_name = row[0]
            us_type = row[header.index('tipo')]
            if us_type in ['property', 'document', 'combiner', 'extractor']:
                if row[header.index('anteriore')] != 'nan' or row[header.index('posteriore')] != 'nan':
                    errors.append(
                        (us_name, "", f"{us_name} è tipo {us_type} ma ha relazione 'anteriore' o 'posteriore'."))
        return errors


    def check_relations(self,rows, header):
        errors = []
        errors.extend(self.check_relation_exists(rows, header))
        errors.extend(self.check_inverse_relation_exists(rows, header))
        errors.extend(self.check_relation_type(rows, header))
        errors.extend(self.check_duplicates(rows, header))
        return errors
    def print_errors_to_textedit(self,errors, text_edit):
        self.textEdit.clear()
        for us_name, related_us_name, error_message in errors:
            #text_edit=self.textEdit
            text_edit.append(f'Errore in row con il nome US"{us_name}" relativo a "{related_us_name}": {error_message}\n')


    ###aggiornamento delle relazioni
    def update_relations(self):

        # Apri il file CSV in lettura
        with open(self.data_file, 'r') as f:
            reader = csv.reader(f)
            # Leggi la prima riga (intestazione) e le righe successive
            header = next(reader)
            rows = list(reader)

        # Crea un dizionario vuoto per memorizzare le righe per nome
        us_dict = {}
        for row in rows:
            us_name = row[0]
            us_dict[us_name] = row

        print(f"rows: {rows}")
        print(f"header: {header}")
        # Funzione interna per aggiornare una relazione
        def update_relation(row, index, relation_type):
            related_us_name = row[index]

            if related_us_name != 'nan':
                # Split related US names by comma
                for related_us in related_us_name.split(','):
                    related_us = related_us.strip()  # Remove possible leading/trailing spaces

                    if related_us not in us_dict:
                        # Crea una nuova riga se B non esiste
                        new_row = [related_us] + ['nan'] * (len(row) - 1)
                        # Aggiungi la relazione inversa
                        if relation_type == 'anteriore':
                            new_row[header.index('posteriore')] = us_name
                        elif relation_type == 'posteriore':
                            new_row[header.index('anteriore')] = us_name
                        elif relation_type == 'properties_ant':
                            new_row[header.index('properties_post')] = us_name
                        elif relation_type == 'properties_post':
                            new_row[header.index('properties_ant')] = us_name

                        us_dict[related_us] = new_row
                        rows.append(new_row)
                    else:
                        # Aggiorna la riga esistente se B esiste
                        existing_row = us_dict[related_us]
                        # Aggiungi la relazione inversa
                        if relation_type == 'anteriore':
                            if existing_row[header.index('posteriore')] == 'nan':
                                existing_row[header.index('posteriore')] = us_name
                            elif us_name not in existing_row[header.index('posteriore')].split(','):
                                existing_row[header.index('posteriore')] += f",{us_name}"
                        elif relation_type == 'posteriore':
                            if existing_row[header.index('anteriore')] == 'nan':
                                existing_row[header.index('anteriore')] = us_name
                            elif us_name not in existing_row[header.index('anteriore')].split(','):
                                existing_row[header.index('anteriore')] += f",{us_name}"
                        elif relation_type == 'properties_ant':
                            if existing_row[header.index('properties_post')] == 'nan':
                                existing_row[header.index('properties_post')] = us_name
                            elif us_name not in existing_row[header.index('properties_post')].split(','):
                                existing_row[header.index('properties_post')] += f",{us_name}"
                        elif relation_type == 'properties_post':
                            if existing_row[header.index('properties_ant')] == 'nan':
                                existing_row[header.index('properties_ant')] = us_name
                            elif us_name not in existing_row[header.index('properties_ant')].split(','):
                                existing_row[header.index('properties_ant')] += f",{us_name}"
        new_rows = []
        # Per ogni riga
        for row in rows:
            us_name = row[0]
            # Se l'unità stratigrafica è di tipo 'property', 'document', 'combiner' o 'extractor'
            if row[header.index('tipo')] in ['property', 'document', 'combiner', 'extractor']:
                # Aggiorna le relazioni 'properties_ant' e 'properties_post'
                update_relation(row, 10, 'properties_ant')  # properties_ant
                update_relation(row, 11, 'properties_post')  # properties_post
            # Se l'unità stratigrafica è di tipo 'contemporaneo'
            elif row[header.index('tipo')] == 'contemporaneo':
                # Aggiorna la relazione 'contemporaneo'
                update_relation(row, 9, 'contemporaneo')  # contemporaneo
            else:
                # Altrimenti, aggiorna le relazioni 'anteriore' e 'posteriore'
                update_relation(row, 7, 'anteriore')  # anteriore
                update_relation(row, 8, 'posteriore')  # posteriore

        rows.extend(new_rows)

        # Dopo aver aggiornato tutte le relazioni, aggiorna la tablewidget
        self.data_table.setRowCount(len(rows))
        self.data_table.setColumnCount(len(header))
        self.data_table.setHorizontalHeaderLabels(header)

        # Riempie la tabella con i dati aggiornati
        for i, row in enumerate(rows):
            for j, item in enumerate(row):
                self.data_table.setItem(i, j, QTableWidgetItem(item))


    def update_relations_google(self):

        try:
            # Carica le credenziali
            creds = Credentials.from_authorized_user_file('credentials.json')

            # Costruisci il servizio gspread
            client = gspread.authorize(creds)

            # Apri il foglio di calcolo
            spreadsheet = client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            QMessageBox.warning(self, 'Attenzione',f"Errore nell'apertura del foglio di calcolo: {e}")
            return

        try:
            # Seleziona il primo foglio di lavoro del foglio di calcolo
            worksheet = spreadsheet.get_worksheet(0)


            # Leggi tutte le righe dal foglio di calcolo
            rows = worksheet.get_all_values()
            header = rows[0]
            rows = rows[1:]

        except Exception as e:
            print(f"Errore nella lettura del foglio di calcolo: {e}")
            returnQMessageBox.warning(self, 'Attenzione',f"Errore nell'apertura del foglio di calcolo: {e}")
            return

        # La prima riga è l'intestazione


        us_dict = {}
        for row in rows:# Rimuovi l'intestazione

            us_name = row[0]
            print(f'us name{us_name}')
            if us_name != header[0]:  # Assicurati di non includere l'intestazione nel dizionario
                us_dict[us_name] = row
        print(f"rows: {us_dict}")
        #print(f"header: {header}")
        # Funzione interna per aggiornare una relazione
        def update_relation(row, index, relation_type):
            related_us_name = row[index]

            if related_us_name != 'nan':
                # Split related US names by comma
                for related_us in related_us_name.split('|'):
                    related_us = related_us.strip()  # Remove possible leading/trailing spaces

                    if related_us not in us_dict:
                        # Crea una nuova riga se B non esiste
                        new_row = [related_us] + ['nan'] * (len(row) - 1)
                        # Aggiungi la relazione inversa
                        if relation_type == 'anteriore':
                            new_row[header.index('posteriore')] = us_name
                        elif relation_type == 'posteriore':
                            new_row[header.index('anteriore')] = us_name
                        elif relation_type == 'properties_ant':
                            new_row[header.index('properties_post')] = us_name
                        elif relation_type == 'properties_post':
                            new_row[header.index('properties_ant')] = us_name

                        us_dict[related_us] = new_row
                        rows.append(new_row)
                    else:
                        # Aggiorna la riga esistente se B esiste
                        existing_row = us_dict[related_us]
                        # Aggiungi la relazione inversa
                        if relation_type == 'anteriore':
                            if existing_row[header.index('posteriore')] == 'nan':
                                existing_row[header.index('posteriore')] = us_name
                            elif us_name not in existing_row[header.index('posteriore')].split('|'):
                                existing_row[header.index('posteriore')] += f"|{us_name}"
                        elif relation_type == 'posteriore':
                            if existing_row[header.index('anteriore')] == 'nan':
                                existing_row[header.index('anteriore')] = us_name
                            elif us_name not in existing_row[header.index('anteriore')].split('|'):
                                existing_row[header.index('anteriore')] += f"|{us_name}"
                        elif relation_type == 'properties_ant':
                            if existing_row[header.index('properties_post')] == 'nan':
                                existing_row[header.index('properties_post')] = us_name
                            elif us_name not in existing_row[header.index('properties_post')].split('|'):
                                existing_row[header.index('properties_post')] += f"|{us_name}"
                        elif relation_type == 'properties_post':
                            if existing_row[header.index('properties_ant')] == 'nan':
                                existing_row[header.index('properties_ant')] = us_name
                            elif us_name not in existing_row[header.index('properties_ant')].split('|'):
                                existing_row[header.index('properties_ant')] += f"|{us_name}"
        new_rows = []
        # Per ogni riga
        for row in rows:
            us_name = row[0]
            # Se l'unità stratigrafica è di tipo 'property', 'document', 'combiner' o 'extractor'
            if row[header.index('tipo')] in ['property', 'document', 'combiner', 'extractor']:
                # Aggiorna le relazioni 'properties_ant' e 'properties_post'
                update_relation(row, 10, 'properties_ant')  # properties_ant
                update_relation(row, 11, 'properties_post')  # properties_post
            # Se l'unità stratigrafica è di tipo 'contemporaneo'
            elif row[header.index('tipo')] == 'contemporaneo':
                # Aggiorna la relazione 'contemporaneo'
                update_relation(row, 9, 'contemporaneo')  # contemporaneo
            else:
                # Altrimenti, aggiorna le relazioni 'anteriore' e 'posteriore'
                update_relation(row, 7, 'anteriore')  # anteriore
                update_relation(row, 8, 'posteriore')  # posteriore

        rows.extend(new_rows)
        print(rows)
        # Dopo aver aggiornato tutte le relazioni, aggiorna la tablewidget
        self.data_table.setRowCount(len(rows))
        self.data_table.setColumnCount(len(header))
        self.data_table.setHorizontalHeaderLabels(header)

        try:
            # Riempie la tabella con i dati aggiornati
            # Inizia da 1 anziché 0 per saltare l'intestazione
            for i, row in enumerate(rows, start=0):
                for j, item in enumerate(row):
                    self.data_table.setItem(i, j, QTableWidgetItem(item))
        except Exception as e:
            QMessageBox.warning(self,'Attenzione',f"Errore nell'aggiornamento della tabella: {e}")
            return
    def update_relationships(self):
        # Leggere i dati dalla QTableWidget e aggiungerli al nuovo DataFrame
        current_df = self.get_current_dataframe()

        # Aggiornare i rapporti nel DataFrame
        updated_df, new_header = self.update_relationships_in_dataframe(current_df)

        # Chiedere all'utente se vuole salvare le modifiche e, se necessario, salvare il file CSV
        #self.ask_to_save_changes(self, updated_df, new_header)
        self.show_errors_in_dock_widget()

    def update_relationships_in_dataframe(self,df):
        with io.StringIO() as buffer:
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            updated_df, new_header = self.transform_data(buffer, buffer)
            buffer.seek(0)
            updated_df = pd.read_csv(buffer, dtype=str)

        return updated_df, new_header

    def show_changes(self,old_rows, new_rows):
        print("Differenze:")
        for old_row, new_row in zip(old_rows, new_rows):
            if old_row != new_row:
                print(f"- Vecchia riga: {old_row}")
                print(f"+ Nuova riga:  {new_row}")
                print()

    def ask_to_save_changes(self, input_csv, output_csv, header, new_rows):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Salva modifiche")
        message_box.setText("Vuoi salvare le modifiche?")
        message_box.setIcon(QMessageBox.Question)
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        result = message_box.exec_()
        if result == QMessageBox.Yes:
            # Salva le modifiche nel file CSV di output
            with open(output_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for row in new_rows:
                    writer.writerow(row)
            print(f"Modifiche salvate in {output_csv}")

            # Ricarica il file CSV di output
            with open(output_csv, 'r') as f:
                reader = csv.reader(f)
                new_header = next(reader)
                new_rows = list(reader)
        else:
            print("Modifiche non salvate.")


    def show_epoch_dialog(self, pos):
        # Get the current cell
        current_cell = self.data_table.itemAt(pos)
        if current_cell is None:
            return
        row, col = current_cell.row(), current_cell.column()
        print(row,col)
        # If the clicked cell is in the "Epoca" column
        if col == 4:
            # Create an EpochDialog instance
            self.epochs_df = pd.read_csv("epoche_storiche.csv")

            # Create a dock widget with the epoch combobox
            epoch_dialog = EpochDialog(self.epochs_df, self)
            selected_epoch = epoch_dialog.get_selected_epoch()
            print(selected_epoch)
            if selected_epoch is not None:

                self.data_table.item(row, col).setData(Qt.DisplayRole, QVariant(selected_epoch))
    def show_unit_dialog(self, pos):
        # Get the current cell
        current_cell = self.data_table.itemAt(pos)
        if current_cell is None:
            return
        row, col = current_cell.row(), current_cell.column()
        print(row,col)
        # If the clicked cell is in the "Epoca" column
        if col == 1:
            # Create an EpochDialog instance
            self.unit_df = pd.read_csv("unita_tipo.csv")

            # Create a dock widget with the epoch combobox
            unit_dialog = UnitDialog(self.unit_df, self)
            selected_unit = unit_dialog.get_selected_unit()
            print(selected_unit)
            if selected_unit is not None:

                self.data_table.item(row, col).setData(Qt.DisplayRole, QVariant(selected_unit))
    def on_google_sheet_action_triggered(self):
        # Check if the spreadsheet ID already exists
        if hasattr(self, 'spreadsheet_id') and self.spreadsheet_id:
            default_id = self.spreadsheet_id
        else:
            try:
                creds = Credentials.from_authorized_user_file('credentials.json')
            except FileNotFoundError:
                creds = self.get_google_sheets_credentials()
            except Exception as e:
                QMessageBox.warning(self, 'Attenzione', f"Errore: {e}")
                return
                return  # Exit the function if an error occurred

            # Costruisci il servizio Drive
            drive_service = build('drive', 'v3', credentials=creds)

            # Esegui una query per trovare tutti i file di tipo Google Spreadsheet
            response = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'").execute()

            # Ottieni l'elenco dei file restituiti
            files = response.get('files', [])

            # Crea una lista di nomi di file
            file_names = [file['name'] for file in files]

            # Mostra un QInputDialog con l'elenco dei nomi dei file
            file_name, ok = QInputDialog.getItem(self, 'Seleziona file', 'Seleziona un file:', file_names, 0, False)

            if ok and file_name:
                # Trova l'ID del file selezionato
                file_id = next((file['id'] for file in files if file['name'] == file_name), None)
                if file_id:
                    print(f"Hai selezionato il file {file_name} con ID {file_id}")
            default_id = file_id

        # Open a QInputDialog with the current ID as the default value
        spreadsheet_id, ok = QInputDialog.getText(self, 'Inserisci ID', 'Inserisci l\'ID dello spreadsheet di Google:',
                                                  text=default_id)

        if ok:
            # Check if the input is not empty
            if spreadsheet_id:
                # Update the spreadsheet ID
                self.spreadsheet_id = spreadsheet_id

                # Range of cells containing the data (e.g., 'Sheet1!A1:C10')
                sheet_range = 'test_banca_dati!A1:L1000'

            #     spreadsheet_id = https://drive.google.com/file/d/1n_InkQij8fkUgQf9r8y3h9YCG_uHC34K/view?usp=share_link'

                # Get and save the credentials
                creds = Credentials.from_authorized_user_file('credentials.json')
                # Read the Google Sheet data and convert it to a pandas DataFrame
                self.df = self.read_google_sheet_to_dataframe(spreadsheet_id, sheet_range,creds)
                print(self.df)
                # Call the transform_data function
                try:
                    buffer = io.StringIO()
                    self.df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    self.transform_data_google(buffer, buffer)
                    buffer.seek(0)
                    self.df = pd.read_csv(buffer, dtype=str)
                except AssertionError as e:
                    print(e)

        #self.df = pd.read_csv(google_df, dtype=str)
        self.data_fields = self.df.columns.tolist()

        self.data_table.setDragEnabled(True)
        # Impostare il numero di righe e colonne nel QTableWidget
        self.data_table.setRowCount(len(self.df))
        self.data_table.setColumnCount(len(self.df.columns))

        # Impostare le etichette delle colonne orizzontali
        self.data_table.setHorizontalHeaderLabels(self.df.columns)

        # Inserire i dati nelle celle del QTableWidget
        for row in range(len(self.df)):
            for col in range(len(self.df.columns)):
                if col == 5:  # Colonna Epoca
                    #combo_box = self.create_epoch_combobox()
                    self.data_table.cellDoubleClicked.connect(self.show_epoch_dialog)
                if col == 2:  # Colonna tipo
                    #combo_box = self.create_epoch_combobox()
                    self.data_table.cellDoubleClicked.connect(self.show_unit_dialog)

                else:
                    item = QTableWidgetItem(str(self.df.iat[row, col]))
                    self.data_table.setItem(row, col, item)

    def save_csv(self):

        # Creare un nuovo DataFrame per salvare i dati dalla QTableWidget
        new_df = pd.DataFrame(columns=self.df.columns)

        # Leggere i dati dalla QTableWidget e aggiungerli al nuovo DataFrame
        for row in range(self.data_table.rowCount()):
            row_data = {}
            for col in range(self.data_table.columnCount()):

                item = self.data_table.item(row, col)
                if item is not None:
                    value = item.text()
                else:
                    value = 'nan'
                row_data[self.df.columns[col]] = value
            new_df = new_df.append(row_data, ignore_index=True)

        # Salvare il nuovo DataFrame nel file CSV
        new_df.to_csv(self.data_file, index=False)
        try:
            self.transform_data(self.data_file, self.data_file)
        except AssertionError:
            pass
        self.df2 = pd.read_csv(self.data_file, dtype=str)
        self.data_fields2 = self.df2.columns.tolist()


        self.data_table.setDragEnabled(True)
        # Impostare il numero di righe e colonne nel QTableWidget
        self.data_table.setRowCount(len(self.df2))
        self.data_table.setColumnCount(len(self.df2.columns))

        # Impostare le etichette delle colonne orizzontali
        self.data_table.setHorizontalHeaderLabels(self.df2.columns)

        # Inserire i dati nelle celle del QTableWidget
        for row in range(len(self.df2)):
            for col in range(len(self.df2.columns)):
                item = QTableWidgetItem(str(self.df2.iat[row, col]))
                self.data_table.setItem(row, col, item)
        for i in range(self.data_table.rowCount()):
            self.data_table.setRowHeight(i, 50)

        for i in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(i, 250)


    def save_google(self):
        # Creare un nuovo DataFrame per salvare i dati dalla QTableWidget
        new_df = pd.DataFrame(columns=self.df.columns, dtype=str)

        # Leggere i dati dalla QTableWidget e aggiungerli al nuovo DataFrame
        for row in range(self.data_table.rowCount()):
            row_data = {}
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                if item is not None:
                    value = item.text()
                else:
                    value = 'nan'
                row_data[self.df.columns[col]] = value
            new_df = new_df.append(row_data, ignore_index=True)

        # Carica le credenziali
        creds = Credentials.from_authorized_user_file('credentials.json')

        # Costruisci il servizio gspread
        client = gspread.authorize(creds)

        # Apri il foglio di calcolo
        spreadsheet = client.open_by_key(self.spreadsheet_id)

        # Seleziona il primo foglio di lavoro del foglio di calcolo
        worksheet = spreadsheet.get_worksheet(0)

        # Scrivi il DataFrame nel foglio di lavoro
        set_with_dataframe(worksheet, new_df)

        # Crea un nuovo DataFrame dai dati del foglio
        #self.df2 = pd.DataFrame(worksheet.get_all_records())
        try:
            buffer = io.StringIO()
            new_df.to_csv(buffer, index=False)
            buffer.seek(0)
            self.transform_data_google(buffer, buffer)
            buffer.seek(0)

        except AssertionError as e:
            print(e)
        self.df2 = pd.read_csv(buffer, dtype=str)
        self.data_fields2 = self.df2.columns.tolist()

        self.data_table.setDragEnabled(True)
        # Impostare il numero di righe e colonne nel QTableWidget
        self.data_table.setRowCount(len(self.df2))
        self.data_table.setColumnCount(len(self.df2.columns))

        # Impostare le etichette delle colonne orizzontali
        self.data_table.setHorizontalHeaderLabels(self.df2.columns)

        # Inserire i dati nelle celle del QTableWidget
        for row in range(len(self.df2)):
            for col in range(len(self.df2.columns)):
                item = QTableWidgetItem(str(self.df2.iat[row, col]))
                self.data_table.setItem(row, col, item)
        for i in range(self.data_table.rowCount()):
            self.data_table.setRowHeight(i, 50)

        for i in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(i, 250)
    def update_csv(self):
        # Aggiorna il DataFrame originale con i dati della QTableWidget
        self.original_df = self.get_current_dataframe()

    def rollback_csv(self):
        # Ripristina i dati della QTableWidget al DataFrame originale
        self.populate_table(self.original_df)

    def populate_table(self, df):
        # Popolare la QTableWidget con i dati del DataFrame
        self.data_table.setRowCount(df.shape[0])
        self.data_table.setColumnCount(df.shape[1])
        self.data_table.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                cell_data = str(df.iloc[row, col])
                self.data_table.setItem(row, col, QTableWidgetItem(cell_data))

    def get_current_dataframe(self):
        # Ottieni il DataFrame corrente dalla QTableWidget
        rows = self.data_table.rowCount()
        cols = self.data_table.columnCount()
        data = []

        for row in range(rows):
            row_data = []
            for col in range(cols):
                item = self.data_table.item(row, col)
                cell_data = item.text() if item is not None else ''
                row_data.append(cell_data)
            data.append(row_data)

        current_df = pd.DataFrame(data, columns=self.df.columns)
        print(data)
        return current_df

    def read_google_sheet_to_dataframe(self, spreadsheet_id, sheet_range, credentials):
        # Build the Sheets API client
        sheets = build('sheets', 'v4', credentials=credentials)

        # Read the data from the Google Sheet
        result = sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=sheet_range).execute()

        # Convert the data to a pandas DataFrame
        data = result.get('values', [])
        df = pd.DataFrame(data[1:], columns=data[0])

        return df

    def get_google_sheets_credentials(self, credentials_file='credentials.json', scopes=None):
        # Use default scopes if none are provided
        if not scopes:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

        # Try loading existing credentials from file
        creds = None
        if os.path.exists(credentials_file):
            creds = Credentials.from_authorized_user_file(credentials_file, scopes)

        # If no valid credentials found, ask user to authenticate
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
            creds = flow.run_local_server(port=0)

            # Save the credentials for next time
            creds_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }

            with open('credentials.json', 'w') as f:
                json.dump(creds_data, f)
            with open('credentials.json', 'r') as f:
                creds_data = json.load(f)

            creds = Credentials.from_authorized_user_info(creds_data)
        return creds

    def load_google_sheet_data(self, spreadsheet_id: str, sheet_range: str, credentials: Credentials) -> pd.DataFrame:
        """
        Load data from a Google Sheet and return it as a Pandas DataFrame.

        Parameters:
            spreadsheet_id (str): The ID of the Google Spreadsheet to load data from.
            sheet_range (str): The A1 notation range of cells to retrieve data from.
            credentials (google.oauth2.credentials.Credentials):
                The Google OAuth2 credentials object with permissions to access the Sheets API.

        Returns:
            pd.DataFrame: A DataFrame containing the data from the Google Sheet
        """

        service = build('sheets', 'v4', credentials=credentials)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range
        ).execute()

        # Convert the data to a Pandas DataFrame
        data = result.get('values', [])
        df = pd.DataFrame(data[1:], columns=data[0])

        return df
    def on_toolButton_load_pressed(self):

        # Open the data CSV file
        self.data_file, _ = QFileDialog.getOpenFileName(self, 'Open Data CSV', '', 'CSV files (*.csv)')
        self.original_df = pd.read_csv(self.data_file)
        if not self.data_file:
            self.show_error('Nessun file selezionato.')
            return
        try:
            self.transform_data(self.data_file,self.data_file)
        except AssertionError:
            pass
        self.df = pd.read_csv(self.data_file, dtype = str)
        self.data_fields = self.df.columns.tolist()

        self.data_table.setDragEnabled(True)
        # Impostare il numero di righe e colonne nel QTableWidget
        self.data_table.setRowCount(len(self.df))
        self.data_table.setColumnCount(len(self.df.columns))

        # Impostare le etichette delle colonne orizzontali
        self.data_table.setHorizontalHeaderLabels(self.df.columns)

        # Inserire i dati nelle celle del QTableWidget
        for row in range(len(self.df)):
            for col in range(len(self.df.columns)):
                    item = QTableWidgetItem(str(self.df.iat[row, col]))
                    self.data_table.setItem(row, col, item)
        for i in range(self.data_table.rowCount()):
            self.data_table.setRowHeight(i, 50)

        for i in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(i, 250)
    def transform_data(self,file_path, output):
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            col1_idx = header.index('anteriore')
            col2_idx = header.index('posteriore')
            col3_idx = header.index('contemporaneo')
            col4_idx = header.index('properties_ant')
            col5_idx = header.index('properties_post')
            rapporti_idx = header.index('rapporti') if 'rapporti' in header else None
            new_header = [col for col in header if col != 'rapporti'] + ['rapporti']
            all_rows = list(reader)

        rows = []
        for row in all_rows:
            if rapporti_idx is not None:
                del row[rapporti_idx]

            col1_values = row[col1_idx].split(',')
            col2_values = row[col2_idx].split(',')
            col3_values = row[col3_idx].split(',')
            col4_values = row[col4_idx].split(',')
            col5_values = row[col5_idx].split(',')


            new_col = []
            for val1 in col1_values:
                if val1:
                    for r in all_rows:
                        if r[0] == val1:
                            new_col.append(['anteriore', val1, r[1], r[3], r[4], r[5], r[6]])

            for val2 in col2_values:
                if val2:
                    for r in all_rows:
                        if r[0] == val2:
                            new_col.append(['posteriore', val2, r[1], r[3], r[4], r[5], r[6]])

            for val3 in col3_values:
                if val3:
                    for r in all_rows:
                        if r[0] == val3:
                            new_col.append(['contemporaneo', val3, r[1], r[3], r[4], r[5], r[6]])

            for val4 in col4_values:
                if val4:
                    for r in all_rows:
                        if r[0] == val4:
                            new_col.append(['properties_ant', val4, r[1], r[3], r[4], r[5], r[6]])

            for val5 in col5_values:
                if val5:
                    for r in all_rows:
                        if r[0] == val5:
                            new_col.append(['properties_post', val5, r[1], r[3], r[4], r[5], r[6]])


            row += [new_col]
            rows.append(row)

        with open(output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(new_header)
            for row in rows:
                writer.writerow(row[:-1] + [' '.join([str(e) for e in row[-1]])])


        self.check_consistency(output,'log.txt')
        self.show_errors_in_dock_widget('log.txt')
    def transform_data_google(self,file_buffer, output_buffer):
        # Read the lines from the StringIO buffer
        lines = file_buffer.readlines()
        reader = csv.reader(lines)
        header = next(reader)
        print(reader)
        col1_idx = header.index('anteriore')
        col2_idx = header.index('posteriore')
        col3_idx = header.index('contemporaneo')
        col4_idx = header.index('properties_ant')
        col5_idx = header.index('properties_post')
        rapporti_idx = header.index('rapporti') if 'rapporti' in header else None
        new_header = [col for col in header if col != 'rapporti'] + ['rapporti']
        all_rows = list(reader)

        rows = []
        for row in all_rows:
            if rapporti_idx is not None:
                del row[rapporti_idx]

            col1_values = row[col1_idx].split('|')
            col2_values = row[col2_idx].split('|')
            col3_values = row[col3_idx].split('|')
            col4_values = row[col4_idx].split('|')
            col5_values = row[col5_idx].split('|')

            new_col = []
            for val1 in col1_values:
                if val1:
                    for r in all_rows:
                        if r[0] == val1:
                            new_col.append(['anteriore', val1, r[1], r[3], r[4], r[5], r[6]])

            for val2 in col2_values:
                if val2:
                    for r in all_rows:
                        if r[0] == val2:
                            new_col.append(['posteriore', val2, r[1], r[3], r[4], r[5], r[6]])

            for val3 in col3_values:
                if val3:
                    for r in all_rows:
                        if r[0] == val3:
                            new_col.append(['contemporaneo', val3, r[1], r[3], r[4], r[5], r[6]])

            for val4 in col4_values:
                if val4:
                    for r in all_rows:
                        if r[0] == val4:
                            new_col.append(['properties_ant', val4, r[1], r[3], r[4], r[5], r[6]])

            for val5 in col5_values:
                if val5:
                    for r in all_rows:
                        if r[0] == val5:
                            new_col.append(['properties_post', val5, r[1], r[3], r[4], r[5], r[6]])
            row += [new_col]
            rows.append(row)

        # Write the transformed data to the output buffer
        output_buffer.seek(0)
        print(output_buffer)
        writer = csv.writer(output_buffer)
        writer.writerow(new_header)
        for row in rows:
            writer.writerow(row[:-1] + [' '.join([str(e) for e in row[-1]])])

        #self.check_consistency_google()
        #self.show_errors_in_dock_widget_google()
    def on_convert_data_pressed(self):
        import time
        data_list, id_us_dict = self.read_transformed_csv(self.data_file)
        CSVMapper.GRAPHML_PATH, _ = QFileDialog.getSaveFileName(self, 'Seleziona la cartella e il nome del file', '',
                                                                'Grapgml Files (*.graphml)')

        # Rimuovi l'estensione dal percorso del file originale
        base_path, _ = os.path.splitext(CSVMapper.GRAPHML_PATH)

        # Ottieni la directory del file originale
        dir_path = os.path.dirname(base_path)
        # config.path = dir_path
        print(f"Config path settato in: {config.path}")
        config.path = os.path.dirname(CSVMapper.GRAPHML_PATH)  # Imposta config.path
        dlg = pyarchinit_Interactive_Matrix(data_list, id_us_dict)
        dlg.generate_matrix()  # Crea il file .dot

        dot_file_path = os.path.join(config.path, "Harris_matrix2ED.dot")  # Percorso completo al file dot

        # Attendi fino a quando il file .dot non esiste o fino a quando non sono passati 10 secondi
        timeout = 10
        start_time = time.time()

        while not os.path.exists(dot_file_path):
            if time.time() - start_time > timeout:
                raise Exception("Timeout while waiting for .dot file to be created.")
            time.sleep(1)  # Aspetta per un secondo


        dottoxml = '{}{}{}'.format('bin', os.sep, 'dottoxml.py')
        try:





            # Crea il percorso al nuovo file dot
            dot_file = os.path.join(dir_path, "Harris_matrix2ED.dot")
            if sys.platform =='win32':

                subprocess.call(['python', dottoxml, '-f', 'Graphml', dot_file, CSVMapper.GRAPHML_PATH], shell=True)
            else:
                subprocess.call(['python3', dottoxml, '-f', 'Graphml', dot_file, CSVMapper.GRAPHML_PATH], shell=True)
            with open(CSVMapper.GRAPHML_PATH, 'r') as file:
                filedata = file.read()

                # Replace the target string
                filedata = filedata.replace("b'", '')
                filedata = filedata.replace("graphml>'", 'graphml>')
                # Write the file out again

            with open(CSVMapper.GRAPHML_PATH, 'w') as file:

                file.write(filedata)
        except KeyError as e:
            QMessageBox.warning(self, "Error", str(e),
                                QMessageBox.Ok)

        #self.d_graph(self.graphml_path)
    def read_transformed_csv(self, file_path):
        data_list = []
        id_us_dict = {}

        with open(file_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)

            # Trova gli indici delle colonne desiderate
            us_idx = header.index("nome us")
            unita_tipo_idx = header.index("tipo")
            descrizione_idx = header.index("descrizione")
            epoca_idx = header.index("epoca")
            e_idx = header.index("epoca index")
            #gruppo_idx = header.index("area")
            rapporti_idx = header.index("rapporti")

            # Leggi e analizza ogni riga
            for row in reader:
                # Estrai i valori dalle colonne desiderate
                us = row[us_idx]
                unita_tipo = row[unita_tipo_idx]
                descrizione = row[descrizione_idx]
                epoca = row[epoca_idx]
                e_id = row[e_idx]
                #gruppo = row[gruppo_idx]
                rapporti_stratigrafici = row[rapporti_idx]

                # Aggiungi i valori a data_list e id_us_dict
                data_list.append([us, unita_tipo, descrizione, epoca,e_id, rapporti_stratigrafici])
                id_us_dict[us] = {"nome_us": us}

        return data_list, id_us_dict

    def check_consistency(self,csv_file, output_file):
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

        us_dict = {}
        for row in rows:
            us_name = row[0]
            us_dict[us_name] = [row[-1]]  # Racchiudiamo row[-1] in una lista

        errors = []
        try:
            for us_name, relations in us_dict.items():
                for relation in relations:
                    relation_type = relation[0]
                    related_us = relation[1]
                    related_relations = us_dict.get(related_us, [])

                    # Check if US exists
                    if not related_relations:
                        errors.append(f"Error: {related_us} not found in the CSV.")
                        continue

                    # Check for consistency in relations
                    inverse_relation_type = ''
                    if relation_type == 'anteriore':
                        inverse_relation_type = 'posteriore'
                    elif relation_type == 'posteriore':
                        inverse_relation_type = 'anteriore'
                    elif relation_type == 'properties_ant':
                        inverse_relation_type = 'properties post'
                    elif relation_type == 'properties post':
                        inverse_relation_type = 'properties_ant'
                    else:  # 'contemporaneo'
                        inverse_relation_type = 'contemporaneo'

                    inverse_relation_found = False
                    for related_relation in related_relations:
                        if related_relation[0] == inverse_relation_type and related_relation[1] == us_name:
                            inverse_relation_found = True
                            break

                    if not inverse_relation_found:
                        errors.append(
                            f"Error: Inconsistent relation between {us_name} ({relation_type}) and {related_us} ({inverse_relation_type}).")

            with open(output_file, 'w') as f:
                if errors:
                    f.write("Errors found:\n")
                    for error in errors:
                        f.write(error + "\n")
                else:
                    f.write("No consistency errors found in the CSV.")
        except:
            pass

    def show_errors_in_dock_widget(self,text):
        #with open('log.txt','r') as f:
            #self.textedit.set
        pass
    def check_consistency_google(self):
        output_buffer = io.StringIO()
        # Convert the DataFrame to a list of rows
        rows = self.df.values.tolist()
        list(rows)

        us_dict = {}
        for row in rows:
            us_name = row[0]
            us_dict[us_name] = [row[-1]]  # Wrap row[-1] in a list

        errors = []
        for us_name, relations in us_dict.items():
            for relation_str in relations:
                # Split the relation_str into a list of strings
                if relation_str is None:
                    continue
                relation = relation_str.split()

                # Check if the relation list has at least 2 elements
                if len(relation) < 2:
                    continue

                relation_type = relation[0]
                related_us = relation[1]
                related_relations = us_dict.get(related_us, [])

                # Check if US exists
                if not related_relations:
                    errors.append(f"Error: {related_us} not found in the CSV.")
                    continue

                # Check for consistency in relations
                inverse_relation_type = ''
                if relation_type == 'anteriore':
                    inverse_relation_type = 'posteriore'
                elif relation_type == 'posteriore':
                    inverse_relation_type = 'anteriore'
                elif relation_type == 'properties_ant':
                    inverse_relation_type = 'properties_post'
                elif relation_type == 'properties_post':
                    inverse_relation_type = 'properties_ant'
                else:  # 'contemporaneo'
                    inverse_relation_type = 'contemporaneo'

                inverse_relation_found = False
                for related_relation_str in related_relations:
                    # Split the related_relation_str into a list of strings
                    related_relation = related_relation_str.split()

                    if related_relation[0] == inverse_relation_type and related_relation[1] == us_name:
                        inverse_relation_found = True
                        break

                if not inverse_relation_found:
                    errors.append(
                        f"Error: Inconsistent relation between {us_name} ({relation_type}) and {related_us} ({inverse_relation_type}).")

        output_buffer.seek(0)
        if errors:
            output_buffer.write("Errors found:\n")
            for error in errors:
                output_buffer.write(error + "\n")
        else:
            output_buffer.write("No consistency errors found in the CSV.")
        return output_buffer.getvalue()
    def show_errors_in_dock_widget_google(self,errors):
        #errors = self.check_consistency_google()
        self.textEdit.setPlainText(errors)

    def show_error(self, message):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText(message)
        dialog.setWindowTitle('Error')
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.show()

    def show_info(self, message):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(message)
        dialog.setWindowTitle('Info')
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.show()


    ###aggiugni righe alla tablewidget
    def on_pushButton_addrow_pressed(self):
        self.add_row()
    def on_pushButton_removerow_pressed(self):
        self.remove_selected_row()

    def add_row(self):
        # Ottieni il numero corrente di righe
        num_rows = self.data_table.rowCount()

        # Inserisci una nuova riga alla fine della tabella
        self.data_table.insertRow(num_rows)
    def remove_selected_row(self):
        # Ottieni gli indici delle righe selezionate
        selected_indexes = self.data_table.selectedIndexes()

        # Se c'è almeno un elemento selezionato
        if selected_indexes:
            # Prendi l'indice della riga del primo elemento selezionato
            row_index = selected_indexes[0].row()

            # Rimuovi la riga corrispondente
            self.data_table.removeRow(row_index)

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():

            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])

            column_count = self.columnCount()

            for column in range(0, column_count):

                if (index.column() == column and role == Qt.TextAlignmentRole):
                    return Qt.AlignHCenter | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if role != Qt.EditRole:
            return False

        row = index.row()

        if row < 0 or row >= self._data.shape[0]:
            return False

        column = index.column()

        if column < 0 or column >= self._data.shape[1]:
            return False

        self._data.iloc[row, column] = value
        self.dataChanged.emit(index, index)

        return True

    def flags(self, index):
        return Qt.ItemIsEnabled



if __name__ == '__main__':
    app = QApplication([])
    mapper = CSVMapper()
    mapper.show()
    app.exec_()