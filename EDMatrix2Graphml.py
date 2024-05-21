import ast
import base64
import shutil
import sys
from functools import partial

import openai
import requests
from PIL import Image
from openai import OpenAI

sys.path.insert(0, "ui")

from modules import splash
import chardet
import mimetypes
from typing import Optional
import re
from PyQt5.QtCore import (QAbstractTableModel, QVariant, pyqtSignal,Qt)
from PyQt5.QtGui import QDesktopServices, QPixmap, QPalette
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType


from modules.interactive_matrix import pyarchinit_Interactive_Matrix
from modules.graph_modeller import *
import json
import csv
import pandas as pd
import gspread
import os
import subprocess
import time
from gspread_dataframe import set_with_dataframe
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import io
from modules.d_graphml import GraphWindow
from modules.load_3d import OBJPROXY
from modules.graphml_to_excel import load_graphml
from modules.check_graphviz_path import check_graphviz
from modules.json2cvs import DataExtractor, DataImporter
from modules.autoswimlane import YEdAutomation
from modules.check_yed_path import YEdSetup
from modules.askgpt import GPT
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from modules.customlistwidget import CustomListWidget
from modules.config import config
from modules.delegateCombobox import ComboBoxDelegate
import sys


MAIN_DIALOG_CLASS, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), 'ui', 'edm2grapml.ui'))

QApplication.setStyle('Fusion')

from PyQt5.QtGui import QIcon



class ImageItem(QListWidgetItem):
    def __init__(self, image_path, text, parent=None):
        super().__init__(parent)

        self.image = QPixmap(image_path)
        self.image_label = QLabel()
        self.image_label.setPixmap(self.image.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.setText(text)
        self.setIcon(QIcon(self.image))  # Imposta l'icona dal QPixmap

    def mousePressEvent(self, event):
        self.image_label.show()



class EnhancedDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = QListWidget()
        self.text_edit = QTextEdit()
        icon_provider = QFileIconProvider()
        # Imposta la dimensione dell'icona
        self.list_widget.setIconSize(QSize(100, 100))

        # Collega il doppio clic del list widget alla funzione show_image
        self.list_widget.itemDoubleClicked.connect(self.handle_double_click)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.text_edit)

        self.container = QWidget()
        self.container.setLayout(self.layout)

        self.setWidget(self.container)
        # Set DockWidget to floating and set it's size
        self.setFloating(True)
        self.resize(500, 500)

        self.mime_to_icon = {
            "application/pdf": "icons/pdf_icon.png",
            "application/msword": "icons/doc_icon.png",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "icons/doc_icon.png",
            "application/vnd.ms-excel": "icons/xls_icon.png",
            "text/csv": "icons/xls_icon.png",
            "text/plain": "icons/doc_icon.png",
            "video/mp4": "icons/video_icon.png",
            "video/x-msvideo": "icons/video_icon.png"
            # ...
        }

    def show_image(self, item):
        # Quando c'è un doppio clic, mostra l'immagine
        item.image_label.show()

    def open_file(self, item):
        QDesktopServices.openUrl(QUrl.fromLocalFile(item.toolTip()))

    def get_icon_for_file(self,filepath):
        # Utilizza il modulo mimetypes per indovinare il tipo MIME del file
        mime_type, _ = mimetypes.guess_type(filepath)
        print(mime_type)
        # Ottieni l'icona appropriata
        icon_path = self.mime_to_icon.get(mime_type,
                                     "icons/default_icon.png")  # Utilizza un'icona predefinita se non ne abbiamo una per il tipo MIME
        icon = QIcon(icon_path)

        return icon


    def handle_double_click(self, item):
        filepath = item.toolTip()  # Ottieni il percorso del file dal "tooltip" dell'elemento
        _, ext = os.path.splitext(filepath)

        # Mostra l'immagine se il file è un'immagine (in base all'estensione del file)
        if ext.lower() in ['.png', '.jpg', '.jpeg']:
            self.show_image(item)
        else:
            self.open_file(item)



    def add_generic_item(self, filepath, name):
        item = QListWidgetItem()
        item.setText(name)
        # Utilizza get_icon_for_file per ottenere e impostare l'icona appropriata
        icon = self.get_icon_for_file(filepath)
        item.setIcon(icon)
        item.setToolTip(filepath)
        # li aggiungo alla listwidget
        self.list_widget.addItem(item)
    def add_image_item(self, image_path, text):
        item = ImageItem(image_path, text)
        self.list_widget.addItem(item)

    def append_text(self, text):
        self.text_edit.append(text)


class EpochDialog(QDialog):
    def __init__(self, epochs_df, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select historical era")
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
        self.cancel_button = QPushButton("Cancel")
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

    def get_selected_epoch(self):
        """
        Returns the selected epoch from the combo box.

        Returns:
            str: The selected epoch if the dialog is accepted, None otherwise.
        """
        if self.exec_() == QDialog.Accepted:
            selected_epoch = self.combo_box.currentText()
            return selected_epoch
        return None
class UnitDialog(QDialog):
    def __init__(self, unit_df, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select unit type")
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
        self.cancel_button = QPushButton("Cancel")
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
        """
        Returns the selected unit from the combo box.

        Returns:
            str: The selected unit.

        Raises:
            None

        Example:
            >>> dialog = Dialog()
            >>> dialog.get_selected_unit()
            'Meter'
        """
        if self.exec_() == QDialog.Accepted:
            selected_units = self.combo_box.currentText()
            selected_unit = selected_units.split('-')[0].strip()
            return selected_unit
        return None



class CSVMapper(QMainWindow, MAIN_DIALOG_CLASS):
        GRAPHML_PATH = None


        def __init__(self, parent=None,data_file=None, spreadsheet=None):

            super(CSVMapper, self).__init__(parent=parent)
            #csv_mapper = CSVMapper()
            #obj_proxy = OBJPROXY(CSVMapper,None)
            self.csv_path = None
            self.obj_proxy = None
            self.df = None
            self.data_fields = None
            self.original_df = None
            self.relationship_data = None
            self.setupUi(self)
            # Crea un'istanza di CustomListWidget
            self.custom_list_widget = CustomListWidget(self)
            self.custom_list_widget.setStyleSheet("background-color: white;")
            self.custom_list_widget.setGeometry(9, 9, 260, 624)
            self.custom_list_widget.setHidden(True)

            # Collega segnali e slot per custom_list_widget
            self.custom_list_widget.itemRemoved.connect(self.on_item_removed)
            print(QStyleFactory.keys())
            self.resize(1000, 1000)
            self.custumize_gui()


            self.data_file = data_file
            self.spreadsheet = spreadsheet
            if data_file is not None:
                self.data_source = 'csv'
            elif spreadsheet is not None:
                self.data_source = 'google_sheet'
            else:
                self.data_source = None
            self.dock_widget = EnhancedDockWidget(self)
            self.dock_widget.setHidden(True)
            self.pushButton_removerow.setHidden(True)
            self.pushButton_addrow.setHidden(True)
            self.data_table.setHidden(True)
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
            self.help_view.load(QUrl.fromLocalFile(os.path.abspath('help/html/help.html')))

            # Crea l'azione Help
            self.help_action = QAction('Help', self)
            # Collega il segnale triggered dell'azione alla funzione show_help
            self.help_action.triggered.connect(self.show_help)
            # Aggiungi l'azione al menu
            self.menu_help_2.addAction(self.help_action)
            # Controlla se la cartella 3dObject è vuota

            if self.data_file is not None:
                csv_directory = os.path.dirname(self.data_file)
                self.object_directory = os.path.join(csv_directory, '3d_obj')

                # Controlla se la cartella 3dObject esiste e non è vuota
                if not os.path.exists(self.object_directory) or not os.listdir(self.object_directory):
                    # Se è vuota o non esiste, disattiva pushButton_3D
                    self.pushButton_3D.setEnabled(False)
            self.pushButton_3D.clicked.connect(self.display_3D)
            self.data_table.currentCellChanged.connect(self.on_table_selection_changed)
            self.search_bar.textChanged.connect(self.search)
            self.graph_modeller.clicked.connect(self.open_graph_modeller)

            self.pushButton_next_rec.clicked.connect(self.next_record)
            self.pushButton_prev_rec.clicked.connect(self.prev_record)

            self.data_table.itemSelectionChanged.connect(self.update_ui_widgets)
            self.tablewidget_change_value()
            # Durante la configurazione dei segnali e degli slot
            self.pushButton_new_rec.clicked.connect(self.clear_line_edits)
            self.update_status_labels()#self.lineEdit_nameus.returnPressed.connect(self.add_text_to_table)
            self.mime_to_icon = {
                "application/pdf": "icons/pdf_icon.png",
                "application/msword": "icons/doc_icon.png",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "icons/doc_icon.png",
                "application/vnd.ms-excel": "icons/xls_icon.png",
                "text/csv": "icons/xls_icon.png",
                "text/plain": "icons/doc_icon.png",
                "video/mp4": "icons/video_icon.png",
                "video/x-msvideo": "icons/video_icon.png"
                # ...
            }
            self.data_table.itemSelectionChanged.connect(self.load_attached_documents)

            self.data_table.itemSelectionChanged.connect(self.handle_row_selection)


        def handle_row_selection(self):
            selected_row = self.data_table.currentRow()
            if selected_row == -1:
                # No row is selected, remove the media list tab if it exists
                self.remove_media_list_tab()
                return

            # Get the value from the second column of the selected row
            type_item = self.data_table.item(selected_row, 1)
            if type_item and type_item.text().lower() in ['property', 'document', 'combiner', 'extractor']:
                # The selected type is one of the specified types, add the media list tab if it's not already there
                self.add_media_list_tab()
            else:
                # The selected type is not one of the specified types, remove the media list tab if it exists
                self.remove_media_list_tab()

        def add_media_list_tab(self):
            # Controlla se custom_list_widget è già aggiunto al widget della scheda
            if self.tabWidget.indexOf(self.custom_list_widget) == -1:
                # Aggiungi custom_list_widget al widget della scheda
                self.tabWidget.addTab(self.custom_list_widget, "Media List")
                icon = QIcon('icon/photo2.png')  # Sostituisci con il percorso del tuo file icona
                self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.custom_list_widget), icon)


        def remove_media_list_tab(self):
            # Trova l'indice del custom_list_widget nel widget della scheda
            index = self.tabWidget.indexOf(self.custom_list_widget)
            if index != -1:
                # Rimuovi la scheda custom_list_widget
                self.tabWidget.removeTab(index)
        def load_attached_documents(self):
            self.custom_list_widget.clear()  # Cancella gli elementi esistenti

            selected_row = self.data_table.currentRow()
            if selected_row == -1:
                return  # Nessuna riga è selezionata

            nameus_item = self.data_table.item(selected_row, 0)
            if not nameus_item:
                return  # La cella "nameus" è vuota
            nameus = nameus_item.text()

            dosco_folder = os.path.join(os.path.dirname(self.data_file), "DosCo")
            if os.path.exists(dosco_folder):
                for file_name in os.listdir(dosco_folder):
                    if file_name.startswith(nameus):  # Controlla se il file corrisponde a 'nameus'
                        file_path = os.path.join(dosco_folder, file_name)
                        mime_type, _ = mimetypes.guess_type(file_path)
                        icon_path = self.mime_to_icon.get(mime_type, "icons/default_icon.png")
                        item = QListWidgetItem(QIcon(icon_path), file_name)
                        self.custom_list_widget.addItem(item)

        def on_item_removed(self, item):
            # Costruisci il percorso completo del file nella cartella "DosCo".
            dosco_folder = os.path.join(os.path.dirname(self.data_file), "DosCo")
            file_path = os.path.join(dosco_folder, item.text())

            # Rimuovere il file se esiste
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            else:
                print(f"File not found: {file_path}")
        def update_status_labels(self):
            # Aggiorna l'etichetta di stato su "corrente"
            self.label_status.setText("current")
            self.label_sort.setText("Not sorted")


            # Aggiorna l'etichetta discografica corrente con l'indice record corrente
            current_record_index = self.get_current_record_index()  # Implementa questo metodo
            self.label_rec_corrente.setText(str(current_record_index))

            #Aggiorna l'etichetta dei record totali con il numero totale di record
            total_records = self.get_total_records()  # Implementa questo metodo
            self.label_rec_tot.setText(str(total_records))

        def get_current_record_index(self):
            # Restituisce l'indice del record attualmente selezionato nella tabella dati
            return self.data_table.currentRow() + 1  # +1 perché le righe sono indicizzate a 0

        def get_total_records(self):
            # Restituisce il numero totale di record nella tabella dati
            return self.data_table.rowCount()

        # Il metodo per cancellare le QLineEdit
        def clear_line_edits(self):
            self.lineEdit_nameus.clear()
            #self.lineEdit_descriptionunit.clear()
            self.lineEdit_epochindex.clear()
            self.comboBox_typeunit.setEditText("")
            self.comboBox_epoch.setEditText("")
            self.textEdit_description.clear()
            self.tableWidget_relationship.clearContents()

        def add_text_to_table(self):
            # Cattura gli input dell'utente
            txt_nameus = self.lineEdit_nameus.text()
            txt_typeunit = self.comboBox_typeunit.currentText()
            #txt_descunit = self.lineEdit_descriptionunit.text()
            txt_epoch = self.comboBox_epoch.currentText()
            txt_epochindex = self.lineEdit_epochindex.text()
            txt_desc = self.textEdit_description.toPlainText()

            # Recupera tutti i dati da QTableWidget
            all_rows = self.get_all_rows()

            # Controlla se txt_nameus esiste già in data_table
            exists = any(self.data_table.item(i, 0) and self.data_table.item(i, 0).text() == txt_nameus
                         for i in range(self.data_table.rowCount()))

            # Crea una nuova riga se txt_nameus non esiste in data_table
            if not exists:
                self.create_new_row(txt_nameus, txt_typeunit, txt_desc, txt_epoch, txt_epochindex)
            else:
                self.update_row(txt_nameus, txt_typeunit, txt_desc, txt_epoch, txt_epochindex)
            # esaminare ogni relazione e aggiornare data_table
            for relationship in all_rows:
                if len(relationship) == 6:
                    self.update_relationship(relationship, txt_nameus, txt_typeunit)


        def remove_or_update_data_table(self, nameus):
            # Implementare la logica per trovare e rimuovere/aggiornare i dati correlati in self.data_table
            for i in range(self.data_table.rowCount()):
                if self.data_table.item(i, 0) and self.data_table.item(i, 0).text() == nameus:
                    # Trovata la riga correlata, ora rimuovila o aggiornala
                    self.data_table.removeRow(i)
                    break

        def refresh_data_table(self):
            # Implementare la logica per aggiornare l'interfaccia utente data_table, se necessario
            self.data_table.viewport().update()

        def update_row(self, nameus, typeunit, desc, epoch, epochindex):
            # Trova la riga esistente
            for i in range(self.data_table.rowCount()):
                if self.data_table.item(i, 0) and self.data_table.item(i, 0).text() == nameus:
                    # Aggiorna i valori
                    self.data_table.setItem(i, 0, QTableWidgetItem(nameus))
                    self.data_table.setItem(i, 1, QTableWidgetItem(typeunit))
                    self.data_table.setItem(i, 3, QTableWidgetItem(desc))
                    self.data_table.setItem(i, 4, QTableWidgetItem(epoch))
                    self.data_table.setItem(i, 5, QTableWidgetItem(epochindex))
                    break

        def get_all_rows(self):
            # Recupera tutti i dati da ogni riga di tableWidget_relationship
            all_rows = []
            for i in range(self.tableWidget_relationship.rowCount()):
                row_data = []
                for j in range(self.tableWidget_relationship.columnCount()):
                    item = self.tableWidget_relationship.item(i, j)
                    row_data.append(item.text() if item else "")
                all_rows.append(row_data)
            return all_rows

        def create_new_row(self, nameus, typeunit,  desc, epoch, epochindex):
            # Crea una nuova riga con i dati forniti e la inserisce in data_table
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            self.data_table.setItem(row_position, 0, QTableWidgetItem(nameus))
            self.data_table.setItem(row_position, 1, QTableWidgetItem(typeunit))
            self.data_table.setItem(row_position, 3, QTableWidgetItem(desc))
            self.data_table.setItem(row_position, 4, QTableWidgetItem(epoch))
            self.data_table.setItem(row_position, 5, QTableWidgetItem(epochindex))

        def update_relationship(self, relationship, nameus, typeunit):
            # Mappatura dei termini inglesi in italiano
            english_to_italian = {
                "anterior": "anteriore",
                "posterior": "posteriore",
                "contemporary": "contemporaneo",
                "properties_ant": "properties_ant",
                "properties_post": "properties_post"
            }
            # Aggiorna la relazione in data_table
            relation_type, related_nameus, related_typeunit, related_desc, related_epoch, related_epochindex = relationship
            # Traduci il relationship_type se è in inglese
            relation_type = english_to_italian.get(relation_type, relation_type)

            print(
                f"Updating relationship: {relation_type}, {related_nameus}, {related_typeunit}, {related_desc}, {related_epoch}, {related_epochindex}")

            # Trova o crea una riga per il relativo "nominaci"
            related_row_position = self.find_or_create_row(related_nameus)

            # Imposta i dati per la riga correlata
            self.data_table.setItem(related_row_position, 0, QTableWidgetItem(related_nameus))
            self.data_table.setItem(related_row_position, 1, QTableWidgetItem(related_typeunit))

            self.data_table.setItem(related_row_position, 3, QTableWidgetItem(related_desc))
            self.data_table.setItem(related_row_position, 4, QTableWidgetItem(related_epoch))
            self.data_table.setItem(related_row_position, 5, QTableWidgetItem(related_epochindex))

            # Trova o crea una riga per il "nominaci" principale
            main_row_position = self.find_or_create_row(nameus)

            # Imposta il tipo principale
            self.data_table.setItem(main_row_position, 1, QTableWidgetItem(typeunit))

            # Per il corrispondente originale 'nome us', aggiorniamo la colonna della relazione opposta
            if relation_type == "anteriore":
                correspondent_relation = "posteriore"
            elif relation_type == "posteriore":
                correspondent_relation = "anteriore"
            elif relation_type == "properties_ant":
                correspondent_relation = "properties_post"
            elif relation_type == "properties_post":
                correspondent_relation = "properties_ant"
            else:
                correspondent_relation = relation_type

            # Aggiorna le colonne di relazione per il "nominaci" originale e correlato
            self.update_relation_item(main_row_position, relation_type, related_nameus)
            self.update_relation_item(related_row_position, correspondent_relation, nameus)

        def update_relation_item(self, row_position, relation_type, nameus):
            # Aggiorna l'elemento della relazione in data_table
            relation_item = self.data_table.item(row_position, self.get_column_index(relation_type))
            current_value = relation_item.text() if relation_item else ''
            new_value = ",".join([current_value, nameus]).lstrip(",")
            self.data_table.setItem(row_position, self.get_column_index(relation_type), QTableWidgetItem(new_value))

        def find_or_create_row(self, nameus):
            # Trova una riga esistente o creane una nuova per il dato "nominaci"
            for i in range(self.data_table.rowCount()):
                if self.data_table.item(i, 0) and self.data_table.item(i, 0).text() == nameus:
                    return i
            # Se non lo trovi, crea una nuova riga
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            return row_position

        def get_column_index(self, relation_type):
            # Mappare il tipo di relazione sull'indice di colonna corretto
            column_indices = {
                'anteriore': 6,
                'posteriore': 7,
                'contemporaneo': 8,
                'properties_ant': 9,
                'properties_post': 10
            }
            return column_indices.get(relation_type, -1)

        def parse_text(self, text):
            # Questa funzione analizza un testo in un
            # formato specifico e restituisce una lista di valori.
            # Se il testo non è nel formato corretto, restituisce una lista vuota.

            text = text.replace("] [", "], [")
            text = "[" + text + "]"
            try:
                print(text)
                print(ast.literal_eval(text))#La funzione  ast.literal_eval()
                # è una funzione del modulo  ast  in Python che valuta in modo
                # letterale l'espressione Python specificata in una stringa.
                # Questa funzione è utile quando si desidera valutare un'espressione
                # Python contenuta in una stringa in modo sicuro, senza eseguire codice
                # dannoso o non sicuro.
                return ast.literal_eval(text)
            except ValueError as er:
                print(f"Could not parse {text}: {str(er)}")
                return []

        def update_ui_widgets(self):
            # Dictionary mapping Italian relationship terms to English
            italian_to_english_relationships = {
                "anteriore": "anterior",
                "posteriore": "posterior",
                "contemporaneo": "contemporary",
                "properties_ant": "properties_ant",
                "properties_post": "properties_post"
            }

            current_row = self.data_table.currentRow()
            current_item_nameus = self.data_table.item(current_row, 0)  # L'indice della colonna dipende da dove si trova il nome.
            current_item_typeunit = self.data_table.item(current_row, 1)
            #current_item_descunit = self.data_table.item(current_row, 2)
            current_item_desc = self.data_table.item(current_row, 3)
            current_item_epoch = self.data_table.item(current_row, 4)
            current_item_epochindex = self.data_table.item(current_row, 5)
            current_item_relationships = self.data_table.item(current_row, 11)

            if current_item_nameus is not None:
                self.lineEdit_nameus.setText(current_item_nameus.text())
            if current_item_typeunit is not None:
                typeunit_text = current_item_typeunit.text()
                if typeunit_text:
                    self.comboBox_typeunit.setCurrentText(typeunit_text)
                else:
                    print("Warning: current_item_typeunit.text() is empty.")
            else:
                print("Warning: current_item_typeunit is None.")


            if current_item_epoch is not None:
                epoch_text = current_item_epoch.text()
                if epoch_text:
                    self.comboBox_epoch.setCurrentText(epoch_text)
                else:
                    print("Warning: current_item_epoch.text() is empty.")
            else:
                print("Warning: current_item_epoch is None.")
            if current_item_epochindex is not None:
                self.lineEdit_epochindex.setText(current_item_epochindex.text())
            if current_item_desc is not None:
                self.textEdit_description.setPlainText(current_item_desc.text())



            if current_item_relationships is not None:
                self.tableWidget_relationship.setRowCount(0)
                self.tableWidget_relationship.setColumnCount(6)  # Poiché ogni relazione ha 6 elementi
                raw_text = current_item_relationships.text()
                relationships = self.parse_text(raw_text)

                for relationship in relationships:
                    row_position = self.tableWidget_relationship.rowCount()
                    self.tableWidget_relationship.insertRow(row_position)
                    for i, item in enumerate(relationship):
                        # Translate the relationship term to English if it's in Italian
                        translated_item = italian_to_english_relationships.get(item, item)
                        print(f"Adding {translated_item} to row {row_position}, column {i}")
                        self.tableWidget_relationship.setItem(row_position, i, QTableWidgetItem(str(translated_item)))

        def insert_or_update_row(self, row_data):
            if 'nome us' in row_data:
                name_us = row_data['nome us']
                if self.original_df is not None:
                    if name_us in self.original_df['nome us'].values:
                        self.original_df.loc[self.original_df['nome us'] == name_us] = pd.Series(row_data)
                    else:
                        self.original_df = self.original_df._append(row_data, ignore_index=True)
                    self.populate_table(self.original_df)
                else:
                    print("self.original_df is None!")
            else:
                print("'nome us' not found in row_data!")

        def delete_row(self, name_us):
            # Delete row where 'name_us' equals the value specified
            self.original_df = self.original_df[self.original_df['nome us'] != name_us]
            self.populate_table(self.original_df)
            self.update_status_labels()

        def on_pushButton_save_mask_pressed(self):
            # Check if the CSV has been loaded
            if self.df is None:
                # Display a message to the user
                QMessageBox.information(self, "No CSV loaded", "Please load a CSV file before saving.")


            self.add_text_to_table()
            for row in range(self.data_table.rowCount()):
                self.row_data = {}
                for col in range(self.data_table.columnCount()):

                    item = self.data_table.item(row, col)
                    if item is not None:
                        value = item.text()
                    else:
                        value = 'nan'
                    self.row_data[self.df.columns[col]] = value
            self.insert_or_update_row(self.row_data)
            print(f"Row data saved: {self.row_data}")
            self.save_to_csv(self.csv_path)
            self.data_table.update()  # aggiorna la tabella
            print(f"{self.csv_path}: Salvato con successo")
            #self.remove_selected_relationship_row()
            self.update_status_labels()
        def save_to_csv(self, csv_filepath):
            #self.original_df=pd.DataFrame()
            self.original_df.to_csv(csv_filepath, index=False)
            self.data_table.update()  # aggiorna la tabella
            print(csv_filepath, 'salvato con successo')

        def next_record(self):
            row_position = self.data_table.currentRow()  # Ottieni la riga attualmente selezionata
            if row_position != -1 and row_position < self.data_table.rowCount() - 1:
                self.data_table.selectRow(row_position + 1)  # Sposta la selezione alla riga successiva
                self.load_data_into_fields()
                self.update_status_labels()
        def prev_record(self):
            row_position = self.data_table.currentRow()  # Ottieni la riga attualmente selezionata
            if row_position != -1 and row_position > 0:
                self.data_table.selectRow(row_position - 1)  # Sposta la selezione alla riga precedente
                self.load_data_into_fields()  # Carica i dati della riga appena selezionata nei campi
                self.update_status_labels()
        # Metodo per caricare i dati della riga selezionata nei campi
        def load_data_into_fields(self):
            fields = [self.lineEdit_nameus, self.comboBox_typeunit,
                      self.textEdit_description,self.textEdit_description,
                      self.comboBox_epoch, self.lineEdit_epochindex]
            row_position = self.data_table.currentRow()

            indices = list(range(5)) + [11]  # Indici delle colonne da cui ottenere i dati
            for i in indices:  # Ora  itererò su questi indici
                if i >= len(fields):
                    continue
                if self.data_table.item(row_position, i):
                    item_text = self.data_table.item(row_position, i).text()
                    if item_text.strip().lower() == 'nan':
                        item_text = None
                    if isinstance(fields[i], QComboBox):
                        fields[i].setCurrentText(item_text)
                    else:
                        fields[i].setText(item_text)

        def tablewidget_change_value(self,row_to_update=None):
            print("Tablewidget_change_value function called")

            numRows = self.tableWidget_relationship.rowCount()
            print(f"Row count: {numRows}")


            # Determine the range of rows to update
            if row_to_update is None:
                start_row = 0
                end_row = self.tableWidget_relationship.rowCount()
            else:
                start_row = row_to_update
                end_row = row_to_update + 1

            for row_position in range(start_row, end_row):
                for j in [0, 2, 4]:  # Columns with comboBoxes
                    comboBox = QComboBox()
                    # ... existing code to populate comboBox with values ...
                    comboBox.currentIndexChanged.connect(
                        lambda index, row=row_position, col=j: self.update_table_value(comboBox, row, col))
                    #self.tableWidget_relationship.setCellWidget(row_position, j, comboBox)

                    #currentIndexChanged.connect(




        # Assuming comboBoxes are in columns 0, 2, and 4, and they represent relationship type, typeunit, and epoch respectively
        def update_table_value(self, comboBox, row, col):
            # Mapping of English terms back to Italian
            english_to_italian = {
                "anterior": "anteriore",
                "posterior": "posteriore",
                "contemporary": "contemporaneo",
                "properties_ant": "properties_ant",
                "properties_post": "properties_post"
            }
            print(f"update_table_value called with row: {row}, col: {col}")
            selected_text = comboBox.currentText()
            print(f"Selected text from comboBox: {selected_text}")

            # Translate the selected English value back to Italian only if it's the relationship type column
            if col == 0:  # Assuming column 0 is the relationship type column
                translated_text = english_to_italian.get(selected_text, selected_text)
            else:
                translated_text = selected_text

            # Retrieve current values for all related fields
            relation_type = self.get_current_value_for_combobox(row, 0) if col != 0 else translated_text
            related_nameus = self.get_current_value_for_combobox(row, 1)  # Assuming column 1 is 'name us'
            related_typeunit = self.get_current_value_for_combobox(row, 2) if col != 2 else translated_text
            related_desc = self.get_current_value_for_combobox(row, 3)  # Assuming column 3 is 'desc'
            related_epoch = self.get_current_value_for_combobox(row, 4) if col != 4 else translated_text
            related_epochindex = self.get_current_value_for_combobox(row, 5)  # Assuming column 5 is 'epochindex'

            # Update the data model
            self.update_data_model(row, col, translated_text)

            # Call update_relationship with the complete set of data
            relationship = (
                relation_type, related_nameus, related_typeunit, related_desc, related_epoch, related_epochindex)
            self.update_relationship(relationship, related_nameus, related_typeunit)

        def update_data_model(self, row, col, value):
            print(f"update_data_model called with row: {row}, col: {col}, value: {value}")
            # check if self.relationship_data is None
            if self.relationship_data is None:
                self.relationship_data = []
            # Assuming self.relationship_data is a list of lists representing the data for each row
            if row < len(self.relationship_data):
                # Ensure the row has enough columns
                while col >= len(self.relationship_data[row]):
                    self.relationship_data[row].append(None)
                # Update the value in the data model
                self.relationship_data[row][col] = value
            else:
                # If the row does not exist, add new rows until the specified row is reached
                while row >= len(self.relationship_data):
                    self.relationship_data.append([None] * self.tableWidget_relationship.columnCount())
                # Now that the row exists, update the value
                self.relationship_data[row][col] = value

            # Update the QTableWidget to reflect the changes
            # First, check if a QTableWidgetItem exists at the specified cell
            item = self.tableWidget_relationship.item(row, col)
            if item is None:
                # If the item does not exist, create it and set it in the table
                item = QTableWidgetItem(value)
                self.tableWidget_relationship.setItem(row, col, item)
            else:
                # If the item exists, simply update its text
                item.setText(value)
        def get_current_value_for_combobox(self, row, column):
            print('funzione get current value for combobox')
            # Retrieve the current value from the QTableWidget or the data model
            item = self.tableWidget_relationship.item(row, column)
            if item:
                return item.text()
            else:
                # If using a QComboBox, get the current text
                comboBox = self.tableWidget_relationship.cellWidget(row, column)
                if comboBox:
                    print(f"comboBox.currentText(): {comboBox.currentText()}")
                    return comboBox.currentText()
                else:
                    return ""  # Return an empty string or a default value if no item or comboBox exists

        def show_message(self, message: str) -> None:
            print(message)
        def yed_path(self):
            yed_setup = YEdSetup()

            yed_path = yed_setup.check_installation()
            if yed_path:
                print(f"yEd is installed at {yed_path}")
                return str(yed_path)


        def open_graph_modeller(self):
            self.graph_modeller = MainWindow()
            self.graph_modeller.show()

        def search(self, text):
            self.data_table.setRowCount(0)  # Clear the table

            if self.df is not None:
                if len(text) >= 3:  # If search text has 3 or more characters
                    # Filter the DataFrame
                    filtered_df = self.df[
                        self.df.apply(
                            lambda row: row.astype(str).str.contains(re.escape(text), case=False, regex=True).any(), axis=1)
                    ]

                    # Update the table with filtered results
                    self.update_table(filtered_df)
                else:  # If search text is cleared or less than 3 characters
                    # Show all data
                    self.update_table(self.df)

        def update_table(self, dataframe):
            self.data_table.setRowCount(0)  # Clear the table before updating
            for index, row in dataframe.iterrows():
                row_index = self.data_table.rowCount()
                self.data_table.insertRow(row_index)
                for col_index, value in enumerate(row.values):
                    self.data_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

        def deselect_proxies(self):
            # Verifica se esiste un oggetto proxy.
            if hasattr(self, 'obj_proxy'):
                # Rimuovi la selezione da tutti gli items nel proxy.
                self.obj_proxy.deselect_all_proxies()


        def display_3D(self):
            #self.deselect_proxies()
            if self.data_file is not None:
                csv_directory = os.path.dirname(self.data_file)
                self.object_directory = os.path.join(csv_directory, '3d_obj')
            self.obj_proxy = OBJPROXY(self,self.object_directory)
            self.obj_proxy.update_models_dir(self.object_directory)
            #self.obj_proxy.mousePressEvent()
            self.tabWidget.insertTab(2, self.obj_proxy, "3D View Time Manager")

        def on_table_selection_changed(self):
            if self.obj_proxy is None:
                print("obj_proxy non è stato inizializzato.")
                return
            self.listWidget_list_media.clear()

            # Get the selected row index
            selected_row = self.data_table.currentRow()
            if selected_row == -1:
                return  # No row is selected

            # Get the 'nameus' value from the first column of the selected row
            nameus_item = self.data_table.item(selected_row, 0)
            if not nameus_item:
                return  # The 'nameus' cell is empty
            nameus = nameus_item.text()

            # Construct the path to the "DosCo" folder relative to the project's CSV file path
            dosco_folder = os.path.join(os.path.dirname(self.data_file), "DosCo")

            # Check if there are documents for the selected 'nameus'
            for file_name in os.listdir(dosco_folder):
                if file_name.startswith(nameus):
                    # Determine the MIME type and select the appropriate icon
                    mime_type, _ = mimetypes.guess_type(file_name)
                    icon_path = self.mime_to_icon.get(mime_type,
                                                      "icons/default_icon.png")  # Use a default icon if MIME type is not found

                    # Create a QListWidgetItem for the file and add it to listWidget_list_media
                    item = QListWidgetItem(QIcon(icon_path), file_name)
                    self.listWidget_list_media.addItem(item)

            # trova il nome dell'oggetto 3d che corrisponde alla riga selezionata
            # supponendo che il nome dell'oggetto 3d sia il contenuto della terza colonna
            tipo = self.data_table.item(selected_row, 1).text()
            mesh_name = self.data_table.item(selected_row, 0).text()

            # divide mesh_name sui slash e prende il primo elemento
            tipo = tipo.split('/')[0]


            meshes_name =tipo+mesh_name+ '.obj'
            self.obj_proxy.deselect_all_proxies()



            print(meshes_name)
            print(self.obj_proxy.meshes.get(meshes_name))
            print(self.obj_proxy.meshes.keys())

            # se il mesh_name corrisponde a una chiave nel dizionario self.obj_proxy.meshes
            if self.obj_proxy.meshes.get(meshes_name) is not None:
                # chiamare `highlight_mesh` su OBJPROXY
                #self.obj_proxy.select_proxy(meshes_name)

                self.obj_proxy.highlight_mesh(meshes_name)

                self.display_related_info(mesh_name)

            descrizione = self.data_table.item(selected_row,
                                               3).text()  # Assumendo che la descrizione sia nella quarta colonna
            self.lineEdit_desc_label.setText(descrizione)


        def get_related_nodes(self, mesh_name):
            # Trova la riga nel DataFrame che corrisponde a mesh_name
            row = self.df.loc[self.df['nome us'] == mesh_name]

            # Se il DataFrame è vuoto, stampa un messaggio e ritorna una lista vuota
            if row.empty:
                print(f"Nessun dato per {mesh_name}")
                return []

            # Unisci le liste da 'properties_ant' e 'properties_post' in una sola lista
            related_nodes = row['properties_ant'].tolist() + row['properties_post'].tolist()

            # Trasforma le stringhe in nodi e rimuovi eventuali stringhe 'nan'
            related_nodes = [node.strip() for nodes in related_nodes if isinstance(nodes, str) for node in nodes.split(',')
                             if
                             node.strip().lower() != 'nan']

            # Crea una copia di related_nodes
            related_nodes_plus = related_nodes.copy()

            # Cerca nodi correlati ai nodi in related_nodes e aggiungi alla lista related_nodes_plus
            for node in related_nodes:
                row = self.df.loc[self.df['nome us'] == node]
                if not row.empty:
                    more_nodes = row['properties_ant'].tolist() + row['properties_post'].tolist()
                    more_nodes = [node.strip() for nodes in more_nodes if isinstance(nodes, str) for node in
                                  nodes.split(',') if
                                  node.strip().lower() != 'nan']
                    related_nodes_plus.extend(more_nodes)

            # Crea una nuova lista per i nodi document
            document_nodes = []

            # Cerca nodi document correlati ai nodi in related_nodes_plus e aggiungi alla lista document_nodes
            for node in related_nodes_plus:
                row = self.df.loc[self.df['nome us'] == node]
                if not row.empty:
                    more_nodes = row['properties_ant'].tolist() + row['properties_post'].tolist()
                    more_nodes = [node.strip() for nodes in more_nodes if isinstance(nodes, str) for node in
                                  nodes.split(',') if
                                  node.strip().lower() != 'nan']
                    document_nodes.extend(more_nodes)

            # Aggiungi i nodi document alla lista finale
            related_nodes_plus.extend(document_nodes)

            # Rimuovo eventuali duplicati convertendo la lista in un set e poi di nuovo in una lista
            related_nodes_plus = list(set(related_nodes_plus))

            print(f"I nodi correlati a {mesh_name} sono {related_nodes_plus}")
            return related_nodes_plus

        def display_related_info(self, mesh_name):
            print(f"Displaying related info for {mesh_name}")
            related_nodes = self.get_related_nodes(mesh_name)

            # Function to retrieve the description of a node from the dataframe
            def get_description_from_df(dataframe, node):
                description = dataframe[dataframe['nome us'] == node]['descrizione'].values[0]
                return description

            # Clear the old info
            self.dock_widget.text_edit.clear()

            # Initialize lists to store various types of nodes
            property_nodes = []
            combiners_nodes = []
            extractors_nodes = []
            document_nodes = []

            # Categorize the nodes into property, combiner, extractor, and document nodes
            for node in related_nodes:
                node_type = self.df[self.df['nome us'] == node]['tipo'].values[0]
                if node_type.startswith('property'):
                    property_nodes.append(node)
                elif node_type in ['combiner']:
                    combiners_nodes.append(node)
                elif node_type in ['extractor']:
                    extractors_nodes.append(node)
                elif node_type == 'document':
                    document_nodes.append(node)

            # Iterate over properties, print their details and related combiners
            for property_node in property_nodes:
                property_description = get_description_from_df(self.df, property_node)
                self.dock_widget.append_text(f"\nProperty (US - {property_node}). Description: {property_description}")

                # Print details of related combiners
                for combiner_node in combiners_nodes:
                    combiner_description = get_description_from_df(self.df, combiner_node)

                    if \
                    self.df[((self.df['properties_ant'] == property_node) | (self.df['properties_post'] == property_node)) &
                            (self.df['nome us'] == combiner_node)].shape[0] > 0:
                        self.dock_widget.append_text(
                            f"\n\tCombiner ({combiner_node}) linked to property. Description: {combiner_description}")


                    # Print details of related extractors
                    for extractor_node in extractors_nodes:
                        extractor_description = get_description_from_df(self.df, extractor_node)

                        if self.df[
                            ((self.df['properties_ant'] == combiner_node) | (self.df['properties_post'] == combiner_node) |
                             (self.df['properties_ant'] == property_node) | (self.df['properties_post'] == property_node)) &
                            (self.df['nome us'] == extractor_node)
                        ].shape[0] > 0:

                            self.dock_widget.append_text(
                                f"\n\tExtractor ({extractor_node}) linked to property. Description: {extractor_description}")

                            # Print details of related documents
                            for document_node in document_nodes:

                                document_description = get_description_from_df(self.df, document_node)

                                if self.df[((self.df['properties_ant'] == extractor_node) | (
                                        self.df['properties_post'] == extractor_node)) |
                                           (self.df['nome us'] == document_node)].shape[0] > 0:

                                    self.dock_widget.append_text(
                                        f"\n\t\tDocument ({document_node}) linked to the Extractor. Description: {document_description}")

            # Se i nodi hanno media
            if self.nodes_have_media(related_nodes):
                self.display_media_in_widget(related_nodes, self.dock_widget)


        def nodes_have_media(self, related_nodes):
            """
            Controlla se i nodi correlati hanno file multimediali associati. Considera che i file multimediali sono archiviati nella directory "DoSco" e
            hanno lo stesso nome del nodo.
            """
            if self.data_file is not None:
                csv_directory = os.path.dirname(self.data_file)
                self.media_directory = os.path.join(csv_directory, 'DosCo')


            print(f"directory dosco{self.media_directory}")
            for node in related_nodes:
                print(node)
                # Check if a file with the same name as the node exists in the media directory
                if os.path.isfile(os.path.join(self.media_directory, node+".png")):
                    return True

            return False

        def display_media_in_widget(self, related_nodes, dock_widget: Optional[EnhancedDockWidget] = None):
            if self.dock_widget is None:
                # Crea un'istanza del widget
                dock_widget = EnhancedDockWidget(self)

            # Rimuove tutti gli elementi esistenti dal QListWidget
            dock_widget.list_widget.clear()

            for node in related_nodes:
                # Assuming media filenames are like node.extension
                for ext in ['jpg', 'docx','jpeg','png', 'pdf', 'doc', 'xls', 'xlsx', 'mp4', 'avi','csv','txt']:
                    media_path = os.path.join(self.media_directory, f"{node}.{ext}")
                    print(media_path)
                    if os.path.isfile(media_path):
                        # For images
                        if ext in ['png', 'jpg', 'jpeg']:
                            dock_widget.add_image_item(media_path, f"{node}.{ext}")
                        # For docs, pdfs and excel files
                        elif ext in ['doc', 'docx', 'pdf']:
                            dock_widget.add_generic_item(media_path, f"{node}.{ext}")  # Need to create this function
                        #for excel
                        elif ext in ['xls', 'xlsx', 'csv', 'txt']:
                            dock_widget.add_generic_item(media_path, f"{node}.{ext}")
                        # For videos

                        elif ext in ['mp4', 'avi']:
                            dock_widget.add_generic_item(media_path, f"{node}.{ext}")  # Need to create this function
                        else:
                            dock_widget.add_generic_item(media_path, f"{node}.{ext}")
                        break  # If we find a file with node's name, we don't check for others

            dock_widget.show()

        def import_graphml(self):

            load_graphml(self.dir_path, self.base_name)
            # Costruisci il percorso al file CSV
            self.csv_path = os.path.join(self.dir_path, self.base_name)

            if os.path.isfile(self.csv_path):
                # Open the data CSV file
                self.data_file = self.csv_path

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
                QMessageBox.warning(self, 'Warning', f"The CSV file {self.csv_path} does not exist")

        def show_help(self):
            self.help_view.show()
        def custumize_gui(self):
            """
            In the cutumize_gui() method, it is setting the window title, setting the geometry,
            and opening files for the template and data CSVs.
            """
            # Add the button to load data from a Google Sheet to the menubar

            google_sheet_action = QAction("Load data from a Google Sheet", self)
            google_sheet_action.triggered.connect(self.on_google_sheet_action_triggered)

            self.update_relationships_button.triggered.connect(self.update_relations)
            self.actionAggiorna_rapporti_Google.triggered.connect(self.update_relations_google)
            self.actionVisualizzatore_3D.triggered.connect(self.d_graph)
            self.actionimport_json.triggered.connect(self.import_json)
            self.actionexport_json.triggered.connect(self.export_json)
            self.actionReport_AI.triggered.connect(self.reportai)
            self.actionAsk_gpt.triggered.connect(self.askgpt_ai)
            self.actionImport_scketch_in_AI.triggered.connect(self.scketchgpt
                                                              )
            def handle_check_relations_action():
                """
                Questa funzione gestisce l'azione di controllo delle relazioni in una tabella dati e di stampa di eventuali errori su QTextEdit.

                Returns:
                    None

                Signature:
                    handle_check_relations_action()

                """
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
            self.actionImport_graphml.triggered.connect(self.import_graphml)
            self.comboBox_typeunit.addItem("")
            self.comboBox_epoch.addItem("")
            typeunit_df = pd.read_csv(os.path.join('template', 'unita_tipo.csv'))
            for index, row in typeunit_df.iterrows():
                self.comboBox_typeunit.addItem(str(row[1]))  # change '0' to column name
            # For epoch
            epoch_df = pd.read_csv(os.path.join('template', 'epoche_storiche.csv'))
            for index, row in epoch_df.iterrows():
                combined_item = str(row[1]) + ' - ' + str(row[2])  # merge second and third column
                self.comboBox_epoch.addItem(combined_item)

        def apikey_gpt(self):
            # HOME = os.environ['PYARCHINIT_HOME']
            #BIN = '{}{}{}'.format(self.HOME, os.sep, "bin")
            api_key = ""
            # Verifica se il file gpt_api_key.txt esiste
            path_key = os.path.join('modules', 'gpt_api_key.txt')
            print(path_key)
            if os.path.exists(path_key):

                # Leggi l'API Key dal file
                with open(path_key, 'r') as f:
                    api_key = f.read().strip()
                    try:

                        return api_key

                    except:
                        reply = QMessageBox.question(None, 'Warning', 'Apikey non valida' + '\n'
                                                     + 'Clicca ok per inserire la chiave',
                                                     QMessageBox.Ok | QMessageBox.Cancel)
                        if reply == QMessageBox.Ok:

                            api_key, ok = QInputDialog.getText(None, 'Apikey gpt', 'Inserisci apikey valida:')
                            if ok:
                                # Salva la nuova API Key nel file
                                with open(path_key, 'w') as f:
                                    f.write(api_key)
                                    f.close()
                                with open(path_key, 'r') as f:
                                    api_key = f.read().strip()
                        else:
                            return api_key


            else:
                # Chiedi all'utente di inserire una nuova API Key
                api_key, ok = QInputDialog.getText(None, 'Apikey gpt', 'Inserisci apikey:')
                if ok:
                    # Salva la nuova API Key nel file
                    with open(path_key, 'w') as f:
                        f.write(api_key)
                        f.close()
                    with open(path_key, 'r') as f:
                        api_key = f.read().strip()

            return api_key
        def reportai(self):
            self.listWidget_ai.clear()
            models = ["gpt-4o"]
            combo = QComboBox()
            combo.addItems(models)
            selected_model, ok = QInputDialog.getItem(self, "Select Model", "Choose a model for GPT:", models, 0,
                                                      False)

            if ok and selected_model:
                # Estrarre la colonna della descrizione dalla tabella self.data_table
                tabella = self.data_table  # Questo è il tuo oggetto QTableWidget
                dati_descrizione = []

                for i in range(tabella.rowCount()):
                    elemento = tabella.item(i, tabella.columnCount() - 1)  # Supponendo che la descrizione sia nell'ultima colonna
                    if elemento is not None:
                        dati_descrizione.append(elemento.text())

                # Unire tutte le descrizioni in una singola stringa
                descriptions = " ".join(dati_descrizione)
                print(descriptions)  # Linea di debug
                os.environ["OPENAI_API_KEY"] = self.apikey_gpt()

                client = OpenAI()

                response= client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "user", "content": f"Let me summarize this table for you. {descriptions}"}
                    ],
                    stream=True
                )

                combined_message = "GPT Response:\n "
                self.listWidget_ai.addItem(combined_message)

                try:
                    end=''

                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            #print(chunk.choices[0].delta.content, end="")
                            combined_message += chunk.choices[0].delta.content
                            combined_message += end
                            self.listWidget_ai.takeItem(self.listWidget_ai.count() - 1)
                            self.listWidget_ai.addItem(combined_message)
                            self.listWidget_ai.scrollToBottom()
                            QApplication.processEvents()
                except requests.exceptions.JSONDecodeError as e:
                    print("Error decoding JSON response:", e)

                    return None

            elif not ok:
                self.listWidget_ai.addItem("Model selection was canceled.")

        def askgpt_ai(self):
            self.listWidget_ai.clear()
            models = ["gpt-4o"]  # Sostituire con i nomi reali dei modelli
            combo = QComboBox()
            combo.addItems(models)
            selected_model, ok = QInputDialog.getItem(self, "Select Model", "Choose a model for GPT", models, 0, False)

            if ok and selected_model:
                # Apri un'interfaccia per fare domande
                question, ok = QInputDialog.getText(self, "Ask GPT", "Enter your question on the table:")

                if ok and question:
                    # Estrarre l'intero set di dati della tabella
                    table = self.data_table  # Questo è il tuo oggetto QTableWidget
                    table_data = []

                    for i in range(table.rowCount()):
                        row_data = []
                        for j in range(table.columnCount()):
                            item = table.item(i, j)
                            if item is not None:
                                row_data.append(item.text())
                        table_data.append(row_data)

                    # Convert table data to a string format
                    table_data_str = "\n".join(["\t".join(row) for row in table_data])
                    print(table_data_str)  # Debugging line

                    os.environ["OPENAI_API_KEY"] = self.apikey_gpt()

                    client = OpenAI()

                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": "user", "content": f"rispondi alle domande inerenti al contenuto di {table_data_str}"
                                                        f"e se necessario genera dei link utili per approfondire"}
                        ],
                        stream=True
                    )

                    combined_message = "GPT Response:\n "
                    self.listWidget_ai.addItem(combined_message)

                    try:
                        end = ''

                        for chunk in response:
                            if chunk.choices[0].delta.content is not None:
                                # print(chunk.choices[0].delta.content, end="")
                                combined_message += chunk.choices[0].delta.content
                                combined_message += end
                                # Rendi i link cliccabili
                                #combined_message = re.sub(r'(https?://\S+)', r'<a href="\1">\1</a>', combined_message)

                                self.listWidget_ai.takeItem(self.listWidget_ai.count() - 1)
                                self.listWidget_ai.addItem(combined_message)
                                #self.listWidget_ai.scrollToBottom()
                                QApplication.processEvents()
                    except requests.exceptions.JSONDecodeError as e:
                        print("Error decoding JSON response:", e)

                        return None

                elif not ok:
                    self.listWidget_ai.addItem("Model selection was canceled.")

        def scketchgpt(self):
            self.listWidget_ai.clear()
            # Apri la finestra di dialogo per selezionare un file immagine
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
            print(file_path)
            if file_path:
                # Estrarre tutti i dati della tabella
                table = self.data_table  # Questo è il tuo oggetto QTableWidget

                # Scorrere la tabella e ottenere tutti gli elementi
                table_data = []
                for r in range(table.rowCount()):  # iterare sulle righe
                    row_data = []
                    for c in range(table.columnCount()):  # iterare sulle colonne
                        item = table.item(r, c)  # ottenere l'elemento alla riga e colonna corrente
                        if item:  # assicurarsi che l'elemento non sia None
                            row_data.append(item.text())
                    table_data.append(row_data)

                    # Converti la lista in stringa.
                table_data_str = "\n".join([" ".join(row) for row in table_data])
                print(f"Table data:\n{table_data_str}")

                prompt = (
                    "Converti le informazioni contenute nell'immagine del diagramma in una tabella con la seguente struttura:\n\n"
                    "Struttura della Tabella:\n\n"
                    "nome us: Identificatore unico dell'unità stratigrafica (US). Se il nodo inizia con US, SF, SU, UTR, USM, USD, VSF, mantieni solo la seconda parte del nome.\n"
                    "tipo: Tipo di nodo (ad esempio, US, USV/s, property). Se il nodo inizia con 'CON', il tipo sarà 'continuity'.\n"
                    "tipo di nodo: Rappresentazione grafica del nodo (ad esempio, rectangle, parallelogram, com.yworks.bpmn.Artifact.withShadow).\n"
                    "descrizione: Descrizione dell'unità stratigrafica.\n"
                    "epoca: Periodo storico associato all'unità stratigrafica.\n"
                    "epoca index: Indice del periodo storico.\n"
                    "anteriore: Unità stratigrafiche precedenti collegate (usa solo il nome us splittato). Inserisci 'nan' se non ci sono informazioni.\n"
                    "posteriore: Unità stratigrafiche successive collegate (usa solo il nome us splittato). Inserisci 'nan' se non ci sono informazioni.\n"
                    "contemporaneo: Unità stratigrafiche contemporanee collegate (usa solo il nome us splittato). Inserisci 'nan' se non ci sono informazioni.\n"
                    "properties_ant: Proprietà associate alle unità stratigrafiche precedenti (usa solo il nome us splittato). Inserisci 'nan' se non ci sono informazioni.\n"
                    "properties_post: Proprietà associate alle unità stratigrafiche successive (usa solo il nome us splittato). Inserisci 'nan' se non ci sono informazioni.\n"
                    "Regole:\n\n"
                    "I nodi che iniziano con US, SF, SU, UTR, USM, USD, VSF devono essere splittati e mantenere solo la seconda parte del nome.\n"
                    "I tipi di nodi combiner, property, document, extractor devono essere inseriti in properties_ant e properties_post.\n"
                    "Gli altri tipi di nodi devono essere inseriti in anteriore, posteriore e contemporaneo.\n"
                    "Se due nodi sono collegati tra loro da un doppio arco, essi sono contemporanei.\n"
                    "Se il nodo inizia con 'CON', il tipo sarà '_continuity'.\n"
                    "Inserisci 'nan' quando non ci sono informazioni disponibili.\n\n"
                    "Esempio di Tabella:\n\n"
                    "nome us\ttipo\ttipo di nodo\tdescrizione\tepoca\tepoca index\tanteriore\tposteriore\tcontemporaneo\tproperties_ant\tproperties_post\n"
                    "1\tUSM\trectangle\tpodio di tempio\tGreek times\t57\tnan\t106\tnan\tnan\tnan\n"
                    "01a\tSF\toctagon\tSpecial Find\tPresent\t0\t01b\tnan\tnan\tnan\tnan\n"
                    "107\tUSV/c\tellipse\tSeries of capitals\tGreek times\t57\t106\tnan\tnan\t107.material,107.dimension,107.shape\tnan\n"
                    "01b\tSF\toctagon\tSpecial Find\tGreek times\t57\t106\t01a\tnan\tD.05.01\tnan\n"
                    "107.material\tproperty\tcom.yworks.bpmn.Artifact.withShadow\tnan\tGreek times\t57\tnan\tnan\tnan\tD.05.01\tnan\n"
                    "D.05.01\textractor\tnan\tnan\tGreek times\t57\t01b\tnan\\tnan\tnan\tnan\t107.material,107.dimension,107.shape\n"
                    "107.dimension\tproperty\tcom.yworks.bpmn.Artifact.withShadow\tnan\tGreek times\t57\tnan\tnan\tnan\tD.05.01\tnan\n"
                    "107.shape\tproperty\tcom.yworks.bpmn.Artifact.withShadow\tnan\tGreek times\t57\tnan\tnan\tnan\tD.05.01\tnan\n"
                    "106.dimension\tproperty\tcom.yworks.bpmn.Artifact.withShadow\tnan\tGreek times\t57\tnan\tnan\tnan\tC.01\tnan\n"
                    "106.shape\tproperty\tcom.yworks.bpmn.Artifact.withShadow\tnan\tGreek times\t57\tnan\tnan\tnan\tC.02\tnan\n"
                    "D.03.01\textractor\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.03\tC.02\n"
                    "D.01.01\textractor\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.01\tC.01\n"
                    "D.01\tdocument\tcom.yworks.bpmn.Artifact.withShadow\tinventory of planimetries in the 2nd BC\tGreek times\t57\tnan\tnan\tnan\tnan\tD.01.01\n"
                    "D.03\tdocument\tcom.yworks.bpmn.Artifact.withShadow\tinventory of planimetries in the 2nd BC\tGreek times\t57\tnan\tnan\tnan\tnan\tD.03.01\n"
                    "C.02\tcombiner\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.03.01,D.02.01\t106.shape\n"
                    "C.01\tcombiner\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.04.01,D.01.01\t106.dimension\n"
                    "D.02.01\textractor\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.02\tC.02\n"
                    "D.02\tdocument\tcom.yworks.bpmn.Artifact.withShadow\tinventory of planimetries in the 2nd BC\tGreek times\t57\tnan\tnan\tnan\tnan\tD.02.01\n"
                    "D.04\tdocument\tcom.yworks.bpmn.Artifact.withShadow\tinventory of planimetries in the 2nd BC\tGreek times\t57\tnan\tnan\tnan\tnan\tD.04.01\n"
                    "D.04.01\textractor\tnan\tnan\tGreek times\t57\tnan\tnan\tnan\tD.04\tC.01\n"
                    "106\tUSV/c\tellipse\tSeries of USV/n\tGreek times\t57\t1\t107,01b\tnan\t106.dimension,106.shape\tnan\n"

                )

                # Passa i dati della tabella al modello GPT.
                gpt_response = GPT.ask_sketch(self, prompt , self.apikey_gpt(), file_path)

                def parse_gpt_response(gpt_response):
                    # Estrarre i dati della tabella dalla risposta del GPT.
                    table_data = []
                    lines = gpt_response.split('\n')
                    start_parsing = False

                    for line in lines:
                        if '| nome us' in line:
                            start_parsing = True
                            continue
                        if start_parsing:
                            if line.startswith('|') and not all(c == '-' for c in line.replace('|', '').strip()):
                                row = [cell.strip() for cell in line.split('|')[1:-1]]
                                table_data.append(row)
                            elif line.strip() == '':
                                break

                    return table_data

                def save_table_as_csv(table_data):
                    headers = [
                        "nome us", "tipo", "tipo di nodo", "descrizione", "epoca", "epoca index",
                        "anteriore", "posteriore", "contemporaneo", "properties_ant", "properties_post", "rapporti"
                    ]

                    # Apri una finestra di dialogo per selezionare la posizione di salvataggio.
                    options = QFileDialog.Options()
                    file_path, _ = QFileDialog.getSaveFileName(None, "Save CSV", "", "CSV Files (*.csv);;All Files (*)",
                                                               options=options)

                    if file_path:
                        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file, delimiter=',')
                            writer.writerow(headers)
                            for row in table_data:
                                writer.writerow(row)

                # Analizzare la risposta GPT per estrarre i dati della tabella
                table_data = parse_gpt_response(gpt_response)

                # Salva i dati estratti dalla tabella in un file CSV
                save_table_as_csv(table_data)


                combined_message = f"GPT Response\n: {gpt_response}"
                self.listWidget_ai.addItem(combined_message)

            else:
                self.listWidget_ai.addItem("Image selection was canceled.")

        def import_json(self):
            file, _ = QFileDialog.getOpenFileName(self, "Select a JSON file", "", "JSON Files (*.json)")
            if file:

                js = DataExtractor(file)
                print(f"Extracting data from {js}")
                extracted_data = js.extract_data()
                print(f"Extracted data: {extracted_data}")
                #Qui ho aggiunto un passaggio di debug per verificare se i dati estratti restituiti da js.extract_data() sono effettivamente un DataFrame di pandas come previsto
                if isinstance(extracted_data, pd.DataFrame):
                    self.df = extracted_data
                    print("Data extraction successful")
                else:
                    print(f"Data extraction failed, expected pandas DataFrame but got {type(extracted_data)}")
                    return  # Uscire dalla funzione perché non possiamo procedere se l'estrazione dei dati è fallita

                self.data_fields = self.df.columns.tolist()

                self.data_table.setDragEnabled(True)
                # Imposta il numero di righe e colonne nel QTableWidget.
                self.data_table.setRowCount(len(self.df))
                self.data_table.setColumnCount(len(self.df.columns))

                # Imposta gli intestazioni delle colonne orizzontali
                self.data_table.setHorizontalHeaderLabels(self.df.columns)

                # Popolare le celle del QTableWidget con i dati
                for row in range(len(self.df)):
                    for col in range(len(self.df.columns)):
                        item = QTableWidgetItem(str(self.df.iat[row, col]))
                        self.data_table.setItem(row, col, item)
                for i in range(self.data_table.rowCount()):
                    self.data_table.setRowHeight(i, 50)

                for i in range(self.data_table.columnCount()):
                    self.data_table.setColumnWidth(i, 250)

                js.export_to_csv('exported_data.csv')

        def export_json(self):
            filename, _ = QFileDialog.getSaveFileName(self, 'Export Data', '', '*.json')
            if filename:  # controllare se l'utente ha scelto un file o annullato il dialogo
                js = DataImporter(self.get_current_dataframe())
                data_to_write = js.to_json_structure()
                with open(filename, "w") as outfile:
                    json.dump(data_to_write, outfile)

        def open_project(self):
            projects_file = 'projects.json'

            # Fornisce un dialogo di selezione del file
            project, _ = QFileDialog.getOpenFileName(self, "Select a project", "", "CSV Files (*.csv)")

            if project:  # Se un file è stato selezionato
                print(f"Opening of the project {project}")

                # Aggiungiamo un blocco try-except per gestire le eccezioni durante l'apertura di un file JSON.
                try:
                    if os.path.isfile(projects_file):
                        with open(projects_file, 'r') as file:
                            projects = json.load(file)
                    else:
                        projects = []
                except Exception as e:
                    QMessageBox.critical(self,'Warning',f"An error occurred while reading the projects file: {str(e)}")
                    return  # Termina la funzione

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
                self.csv_path = os.path.join(os.path.dirname(project), f"{base_name_no_ext}.csv")

                if os.path.isfile(self.csv_path):
                    self.data_file = self.csv_path

                    try:
                        # gestire eccezioni durante la trasformazione dei dati e la lettura di CSV
                        self.transform_data(self.data_file, self.data_file)
                        self.df = pd.read_csv(self.data_file, dtype=str)
                    except Exception as e:
                        QMessageBox.critical(self,'Warning',f"An error occurred while transforming data or reading CSV: {str(e)}")
                        return  # Termina la funzione


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
                    self.data_table.selectRow(0)
                    self.update_status_labels()
                    self.load_attached_documents()
                else:
                    QMessageBox.warning(self,'Warning',f"The CSV file {self.csv_path} does not exist")

        def open_recent_project(self):
            """
            Apre un progetto recente selezionato dall'utente.

            Parametri:
            - self: l'istanza attuale della classe.

            Restituisce:
            None

            Eccezioni:
            None

            Descrizione:
            - Legge il file 'projects.json' per ottenere un elenco di progetti recenti.
            - Visualizza una finestra di dialogo per consentire all'utente di selezionare un progetto.
            - Se viene selezionato un progetto, apre il progetto e esegue i seguenti passaggi:
                - Stampa un messaggio che indica il progetto aperto.
                - Esegue l'estrazione del nome di base del file del progetto.
                - Costruisce il percorso al file CSV corrispondente.
                - Se il file CSV esiste, esegue le azioni seguenti:
                    - Imposta l'attributo del file dati della classe sul percorso del file CSV.
                    - Trasforma i dati nel file CSV.
                    - Legge il file CSV in un DataFrame di pandas.
                    - Imposta l'attributo dei campi dati della classe sulle colonne del DataFrame.
                    - Imposta il numero di righe e colonne nel widget della tabella dati.
                    - Imposta le etichette dell'intestazione orizzontale del widget della tabella dati.
                    - Popola il widget della tabella dati con i dati del DataFrame.
                    - Imposta l'altezza delle righe e la larghezza delle colonne del widget della tabella dati.
                - Se il file CSV non esiste, visualizza un messaggio di avviso.

            Nota:
            - Questa funzione presuppone l'esistenza del file 'projects.json' nella directory corrente.
            - Questa funzione si basa sulla disponibilità delle classi QInputDialog, QMessageBox e QTableWidgetItem.
            """
            projects_file = 'projects.json'

            if os.path.isfile(projects_file):
                with open(projects_file, 'r') as file:
                    projects = json.load(file)

                project, ok = QInputDialog.getItem(self, "Select a recent project", "Projects:", projects, 0, False)
                if ok and project:
                    # qui puoi implementare il codice per aprire il progetto selezionato
                    print(f"Opening of the project {project}")

                    # Get the base name of the project
                    base_name = os.path.basename(project)
                    base_name_no_ext = os.path.splitext(base_name)[0]  # Rimuovi l'estensione del file

                    # Costruisci il percorso al file CSV
                    self.csv_path = os.path.join(project, f"{base_name_no_ext}.csv")

                    if os.path.isfile(self.csv_path):
                        # Open the data CSV file
                        self.data_file = self.csv_path

                        try:
                            self.transform_data(self.data_file, self.data_file)
                        except AssertionError:
                            pass
                        # Use chardet to detect the encoding of the CSV file
                        with open(self.data_file, 'rb') as f:
                            rawdata = f.read()
                        result = chardet.detect(rawdata)
                        charenc = result['encoding']

                        # If chardet is unable to detect the encoding, default to 'ISO-8859-1'
                        if charenc is None:
                            charenc = 'ISO-8859-1'

                        try:
                            self.df = pd.read_csv(self.data_file, dtype=str, encoding=charenc)
                        except UnicodeDecodeError:
                            # If a UnicodeDecodeError occurs, try reading the file with 'ISO-8859-1' encoding
                            self.df = pd.read_csv(self.data_file, dtype=str, encoding='ISO-8859-1')

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
                        self.data_table.selectRow(0)
                        self.update_status_labels()
                        self.load_attached_documents()
                    else:
                        QMessageBox.warning(self,'Warning',f"The CSV file {self.csv_path} does not exist")


        def save_project_to_json(self, project_dir):
            """
            Saves the given project directory to a JSON file.

            Args:
                self: The current instance of the class.
                project_dir (str): The directory of the project to be saved.

            Returns:
                None

            Raises:
                None

            Example:
                save_project_to_json(self, '/path/to/project')

            This function loads the existing projects from a JSON file, inserts the given project directory at the beginning of the list,
            and then saves the updated list back to the JSON file. If the JSON file does not exist, it creates a new one.

            The maximum number of projects that can be stored in the JSON file is 5. If the list exceeds this limit, the oldest projects
            are removed from the list before saving.

            Note:
                - The JSON file should be named 'projects.json' and should be located in the same directory as the script.
                - The projects are stored as a list of strings representing the project directories.
            """
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
            # Seleziona la cartella e il nome del file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fname, _ = QFileDialog.getSaveFileName(self, 'Select the folder and file name', '',
                                                   'CSV Files (*.csv)', options=options)
            # Aggiungi l'estensione .csv se l'utente non l'ha già fatto
            if not fname.endswith(".csv"):
                fname += ".csv"

            if fname:
                # Crea le directory in modo sicuro
                self.dir_path = os.path.dirname(fname)
                self.base_name = os.path.basename(fname)
                #base_name_no_ext = os.path.splitext(base_name)[0]  # Rimuovi l'estensione del file

                try:
                    os.makedirs(self.dir_path, exist_ok=True)
                    os.makedirs(os.path.join(self.dir_path, "DosCo"), exist_ok=True)
                    os.makedirs(os.path.join(self.dir_path, "3d_obj"), exist_ok=True)
                except OSError as e:
                    QMessageBox.critical(None, "Error", f"Error creating directories: {e}")
                    return

                # Subito dopo, includo la funzione per copiare i file
                src_dir = 'modules/icons'  # specificare il percorso assoluto se necessario
                dst_dir = os.path.join(self.dir_path, "3d_obj")
                file_names = os.listdir(src_dir)
                for file_name in file_names:
                    # Aggiungo un controllo per l'estensione .png
                    if file_name.endswith('.png'):
                        shutil.move(os.path.join(src_dir, file_name), dst_dir)
                # Crea il file CSV in modo sicuro
                self.csv_path = os.path.join(self.dir_path, self.base_name)
                try:
                    with open(self.csv_path, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['nome us', 'tipo', 'tipo di nodo', 'descrizione', 'epoca', 'epoca index',
                                         'anteriore', 'posteriore', 'contemporaneo',
                                         'properties_ant', 'properties_post'])
                except OSError as e:
                    QMessageBox.critical(None, "Error", f"Error creating CSV file: {e}")
                    return

                # Salva i dettagli del progetto
                self.save_project_to_json(self.dir_path)

                # Open the data CSV file
                self.data_file = self.csv_path

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
            """
            Opens a 3D graph viewer using the GraphML file specified in CSVMapper.GRAPHML_PATH.

            If CSVMapper.GRAPHML_PATH is not defined, an error message is displayed and the function returns.

            If the GraphML file does not exist in the specified path, a warning message is displayed and the user is prompted
            to choose an alternate path. If a valid alternate path is provided, the GraphML file is loaded using the alternate path.
            If the alternate path is invalid or not provided, an error message is displayed and the function returns.

            If the GraphML file is successfully loaded, the 3D graph viewer is launched using the loaded file.

            Raises:
                None

            Returns:
                None
            """
            graphml_path = CSVMapper.GRAPHML_PATH

            # Verifica se il percorso CSVMapper.GRAPHML_PATH è stato definito
            if graphml_path is None:
                QMessageBox.critical(None, "Errore",
                                     "la path non è stata definita correttamente.\n"
                                     "Dovrai caricare un csv valido e convertire prima di utilizzare il visualizzatore 3D")
                return
                #continue

            # Verifica se il file GraphML esiste nel percorso specificato
            if graphml_path and not os.path.isfile(graphml_path):
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("Il file GraphML non esiste nel percorso specificato.")
                msg_box.setInformativeText("Scegliere un percorso alternativo per caricare il file.")
                msg_box.setWindowTitle("File non trovato")
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg_box.setDefaultButton(QMessageBox.Ok)

                # Mostra la finestra di dialogo
                result = msg_box.exec()

                if result == QMessageBox.Ok:
                    # Mostra la finestra di dialogo per l'inserimento del percorso alternativo
                    alternate_path, ok_pressed = QInputDialog.getText(None, "Percorso alternativo",
                                                                      "Inserisci il percorso del file GraphML:")
                    if ok_pressed and os.path.isfile(alternate_path):
                        graphml_path = alternate_path
                    else:
                        QMessageBox.warning(None, "Errore",
                                            "Il percorso fornito non esiste o non è un file valido. Caricamento del file GraphML non riuscito.")
                        return
                else:
                    return

            try:# Cerca se yed è installato, se lo è, carica il file graphml in yed e poi chiama la finestra 3D.
                # Carica il visualizzatore 3D
                yed_path = self.yed_path()
                graphml_path = graphml_path

                yed_auto = YEdAutomation(yed_path, graphml_path)
                yed_auto.launch_yed()
                yed_auto.bring_yed_to_foreground()
                yed_auto.apply_swimlane_layout()
                yed_auto.save_file()
                #yed_auto.close_yed()
                GraphWindow(graphml_path)
            except Exception as e:
                print(e)
                QMessageBox.critical(self,'Attenzione','Il graphml non è stato aperto con yed e lanciato\n'
                                                       'lo swimlane.\n'
                                                       'Ricordati di salvare in yed il graphml prima di usare il visualizzatore')



        #serie di funzioni per cercare gli errori nelle relazioni
        # cerca duplicati nella stessa riga
        # cerca se le relazioni esistono
        # se le relazioni inverse esistono
        # il tipo di relazione se è corretto
        def check_duplicates(self, rows, header):
            """
            Check for duplicates in the given rows based on the specified header.

            Args:
                self: The object instance.
                rows (List[List[str]]): The rows containing the data to be checked.
                header (List[str]): The header specifying the columns to be checked.

            Returns:
                List[Tuple[List[str], str]]: A list of tuples containing the duplicate values and an error message.

            Example:
                rows = [['John', 'Doe', 'anteriore', 'anteriore', 'properties_ant'],
                        ['Jane', 'Smith', 'posteriore', 'properties_post', 'properties_post']]
                header = ['First Name', 'Last Name', 'Relation Type 1', 'Relation Type 2', 'Relation Type 3']
                check_duplicates(rows, header)
                # Output: [(['anteriore', 'anteriore'], "['anteriore', 'anteriore'] è duplicato"),
                #          (['properties_post', 'properties_post'], "['properties_post', 'properties_post'] è duplicato")]
            """
            errors = []
            for row in rows:
                for relation_type in ['anteriore', 'posteriore', 'properties_ant', 'properties_post']:
                    if relation_type in header:
                        related_us_names = row[header.index(relation_type)]
                        if related_us_names != 'nan':
                            related_us_names = related_us_names.split(',')
                            if len(related_us_names) != len(set(related_us_names)):
                                errors.append((related_us_names), f"{related_us_names} is duplicated")
            return errors
        def check_relation_exists(self,rows, header):
            '''
            La funzione prende 3 argomenti: l'oggetto stesso, `rows`, e `header`.
            L'oggetto stesso rappresenta l'istanza della classe, mentre `rows` è una lista di righe di dati e `header`
            è una lista di intestazioni di colonna.

            Questa funzione serve a controllare se le relazioni nel file esistono realmente. Analizza ogni riga nella lista
            `rows` e controlla se una relazione è presente per ogni tipo di relazione specificato in una lista. Se una
            relazione è presente, viene controllato se l'altro elemento della relazione esiste nelle righe di dati.
            Se non esiste, viene aggiunto un errore alla lista `errors`.

            Il codice utilizza un ciclo `for` per attraversare ogni riga nella lista `rows`. Per ogni riga,
            viene preso il nome dell'elemento `us_name` dalla colonna 0. Successivamente, viene attraversata una lista di
            tipi di relazione e per ogni tipo di relazione, viene preso il nome degli elementi correlati dalla colonna
            corrispondente nell'elenco `header`.

            Se i nomi degli elementi correlati non sono 'nan', vengono divisi in una lista di nomi singoli e controllati
            se esistono nelle righe di dati. Se un nome correlato non viene trovato, viene aggiunto un errore alla lista `errors`.

            Infine, viene restituita la lista di errori
                    Parameters
                    ----------
                    rows
                    header

                    Returns
                    -------

                    '''
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
                                               f"{us_name} è relazionato a {related_us_name} ma {related_us_name} non esiste."))
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
                                               f"{us_name} has a {relation_type} relationship with {related_us_name} but {related_us_name} not has a  {inverse_relation_type} relationship whith {us_name}."))
            return errors
        def check_relation_type(self,rows, header):
            errors = []
            for row in rows:
                us_name = row[0]
                us_type = row[header.index('tipo')]
                if us_type in ['property', 'document', 'combiner', 'extractor']:
                    if row[header.index('anteriore')] != 'nan' or row[header.index('posteriore')] != 'nan':
                        errors.append(
                            (us_name, "", f"{us_name} is type {us_type} but has relationship 'anteriore' or 'posteriore'."))
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
                text_edit.append(f'Error in row with name US"{us_name}" relative to "{related_us_name}": {error_message}\n')


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
                    update_relation(row, 9, 'properties_ant')  # properties_ant
                    update_relation(row, 10, 'properties_post')  # properties_post
                # Se l'unità stratigrafica è di tipo 'contemporaneo'
                elif row[header.index('tipo')] == 'contemporaneo':
                    # Aggiorna la relazione 'contemporaneo'
                    update_relation(row, 8, 'contemporaneo')  # contemporaneo
                else:
                    # Altrimenti, aggiorna le relazioni 'anteriore' e 'posteriore'
                    update_relation(row, 6, 'anteriore')  # anteriore
                    update_relation(row, 7, 'posteriore')  # posteriore

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
                QMessageBox.warning(self, 'Warning',f"Error opening spreadsheet: {e}")
                return

            try:
                # Seleziona il primo foglio di lavoro del foglio di calcolo
                worksheet = spreadsheet.get_worksheet(0)


                # Leggi tutte le righe dal foglio di calcolo
                rows = worksheet.get_all_values()
                header = rows[0]
                rows = rows[1:]

            except Exception as e:
                print(f"Error reading spreadsheet: {e}")
                QMessageBox.warning(self, 'Warning',f"Error opening spreadsheet: {e}")
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
                QMessageBox.warning(self,'Warning',f"Error updating table: {e}")
                return
        def update_rapporti(self):
            # Leggere i dati dalla QTableWidget e aggiungerli al nuovo DataFrame
            current_df = self.get_current_dataframe()

            # Aggiornare i rapporti nel DataFrame
            updated_df, new_header = self.update_rapporti_in_dataframe(current_df)

            # Chiedere all'utente se vuole salvare le modifiche e, se necessario, salvare il file CSV
            #self.ask_to_save_changes(self, updated_df, new_header)
            self.show_errors_in_dock_widget()

        def update_rapporti_in_dataframe(self,df):
            with io.StringIO() as buffer:
                df.to_csv(buffer, index=False)
                buffer.seek(0)
                updated_df, new_header = self.transform_data(buffer, buffer)
                buffer.seek(0)
                updated_df = pd.read_csv(buffer, dtype=str)

            return updated_df, new_header

        def show_changes(self,old_rows, new_rows):
            print("Difference:")
            for old_row, new_row in zip(old_rows, new_rows):
                if old_row != new_row:
                    print(f"- Old line: {old_row}")
                    print(f"+ New line:  {new_row}")
                    print()

        def ask_to_save_changes(self, input_csv, output_csv, header, new_rows):
            message_box = QMessageBox(self)
            message_box.setWindowTitle("Save Changes")
            message_box.setText("Do you want to save the changes?")
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
                print(f"Changes saved in {output_csv}")

                # Ricarica il file CSV di output
                with open(output_csv, 'r') as f:
                    reader = csv.reader(f)
                    new_header = next(reader)
                    new_rows = list(reader)
            else:
                print("Changes not saved.")

        def show_epoch_dialog(self, pos):
            # Verifica se la posizione è valida
            if not self.data_table.indexAt(pos).isValid():
                return
            print(pos)
            # Ottieni la cella corrente
            current_cell = self.data_table.itemAt(pos)
            if current_cell is None:
                return

            row, col = current_cell.row(), current_cell.column()

            # Se la cella cliccata è nella colonna "Epoca"
            if col == 4:
                # Crea un'istanza di EpochDialog
                self.epochs_df = pd.read_csv("template/epoche_storiche.csv")

                # Crea un dock widget con la combobox delle epoche
                epoch_dialog = EpochDialog(self.epochs_df, self)
                selected_epoch = epoch_dialog.get_selected_epoch()
                print(selected_epoch)
                if selected_epoch is not None:
                    # Imposta il valore selezionato nella cella
                    item = QTableWidgetItem(str(selected_epoch))
                    item.setData(Qt.DisplayRole, QVariant(selected_epoch))
                    self.data_table.setItem(row, col, item)

        def show_unit_dialog(self, pos):
            # Verifica se la posizione è valida
            if not self.data_table.indexAt(pos).isValid():
                return

            # Ottieni la cella corrente
            current_cell = self.data_table.itemAt(pos)
            if current_cell is None:
                return

            row, col = current_cell.row(), current_cell.column()

            # Se la cella cliccata è nella colonna "Unità"
            if col == 1:
                # Crea un'istanza di UnitDialog
                try:
                    self.unit_df = pd.read_csv("template/unita_tipo.csv")
                except FileNotFoundError:
                    QMessageBox.critical(None, "Error", "File unit_type.csv not found.")
                    return

                # Crea un dock widget con la combobox delle unità
                unit_dialog = UnitDialog(self.unit_df, self)
                selected_unit = unit_dialog.get_selected_unit()
                print(selected_unit)
                if selected_unit is not None:
                    # Imposta il valore selezionato nella cella
                    item = QTableWidgetItem(str(selected_unit))
                    item.setData(Qt.DisplayRole, QVariant(selected_unit))
                    self.data_table.setItem(row, col, item)
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
                    QMessageBox.warning(self, 'Warning', f"Error:{e}")
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
                file_name, ok = QInputDialog.getItem(self, 'Select file', 'Select a file:', file_names, 0, False)

                if ok and file_name:
                    # Trova l'ID del file selezionato
                    file_id = next((file['id'] for file in files if file['name'] == file_name), None)
                    if file_id:
                        print(f"You have selected the file {file_name} with ID{file_id}")
                default_id = file_id

            # Open a QInputDialog with the current ID as the default value
            spreadsheet_id, ok = QInputDialog.getText(self, 'Enter ID', 'Enter Google spreadsheet ID:',
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
            # Create a new DataFrame to save data from QTableWidget
            new_df = pd.DataFrame(columns=self.df.columns)

            # Read data from QTableWidget and add to new DataFrame
            for row in range(self.data_table.rowCount()):
                self.row_data = {}
                for col in range(self.data_table.columnCount()):

                    item = self.data_table.item(row, col)
                    if item is not None:
                        value = item.text()
                    else:
                        value = 'nan'
                    self.row_data[self.df.columns[col]] = value
                # print(type(new_df))
                new_df = new_df._append(self.row_data, ignore_index=True)

            # Salva il nuovo DataFrame nel file CSV
            new_df.to_csv(self.data_file, index=False, encoding='utf-8')

            try:
                self.transform_data(self.data_file, self.data_file)
            except AssertionError:
                pass

            # Usa chardet per scoprire la codifica
            rawdata = open(self.data_file, 'rb').read()
            result = chardet.detect(rawdata)
            charenc = result['encoding']

            # Read the CSV file back into self.df2 using the detected encoding
            try:
                self.df2 = pd.read_csv(self.data_file, dtype=str, encoding=charenc)
            except UnicodeDecodeError:
                # If a UnicodeDecodeError occurs, try reading the file with 'ISO-8859-1' or 'latin1' encoding
                self.df2 = pd.read_csv(self.data_file, dtype=str, encoding='utf-8')

            self.data_fields2 = self.df2.columns.tolist()

            self.data_table.setDragEnabled(True)
            # Set the number of rows and columns in the QTableWidget
            self.data_table.setRowCount(len(self.df2))
            self.data_table.setColumnCount(len(self.df2.columns))

            # Set horizontal column labels
            self.data_table.setHorizontalHeaderLabels(self.df2.columns)

            # Enter data in the cells of QTableWidget
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
                self.row_data = {}
                for col in range(self.data_table.columnCount()):
                    item = self.data_table.item(row, col)
                    if item is not None:
                        value = item.text()
                    else:
                        value = 'nan'
                    self.row_data[self.df.columns[col]] = value
                new_df = new_df.append(self.row_data, ignore_index=True)

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
                self.row_data = []
                for col in range(cols):
                    item = self.data_table.item(row, col)
                    cell_data = item.text() if item is not None else ''
                    self.row_data.append(cell_data)
                data.append(self.row_data)

            # Check if columns in data matches with self.df
            if len(data[0]) == len(self.df.columns):
                current_df = pd.DataFrame(data, columns=self.df.columns)
            else:
                print("Error: mismatch in number of columns in data and self.df")
                return None

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
            self.data_table.selectRow(0)
            return df

        def on_toolButton_load_pressed(self):
            # Open the data CSV file
            self.data_file, _ = QFileDialog.getOpenFileName(self, 'Open Data CSV', '', 'CSV files (*.csv)')

            # Verify if file exists and is not empty
            if not self.data_file:
                self.show_error('No file selected.')
                return

            # Use chardet to detect the encoding of the CSV file
            with open(self.data_file, 'rb') as f:
                rawdata = f.read()
            result = chardet.detect(rawdata)
            charenc = result['encoding']

            # If chardet is unable to detect the encoding, default to 'ISO-8859-1'
            if charenc is None:
                charenc = 'utf-8'

            # Read data and handle possible errors
            try:
                self.original_df = pd.read_csv(self.data_file, dtype=str, encoding=charenc)
            except Exception as e:
                self.show_error(f"Error reading file: {e}")
                return
            # Verify if the data is empty
            if self.original_df.empty:
                self.show_error('The selected file is empty.')
                return

            # Transform data and handle possible errors
            try:
                self.transform_data(self.data_file, self.data_file)
            except Exception as e:
                self.show_error(f"Error during data transformation: {e}")
                return

            # Set the DataFrame to the original DataFrame after transformation
            self.df = self.original_df
            self.data_fields = self.df.columns.tolist()

            self.data_table.setDragEnabled(True)
            # Set the number of rows and columns in the QTableWidget
            self.data_table.setRowCount(len(self.df))
            self.data_table.setColumnCount(len(self.df.columns))

            # Set the labels of the horizontal columns
            self.data_table.setHorizontalHeaderLabels(self.df.columns)

            # Insert data into the cells of the QTableWidget
            for row in range(len(self.df)):
                for col in range(len(self.df.columns)):
                    item = QTableWidgetItem(str(self.df.iat[row, col]))
                    self.data_table.setItem(row, col, item)
            for i in range(self.data_table.rowCount()):
                self.data_table.setRowHeight(i, 50)

            for i in range(self.data_table.columnCount()):
                self.data_table.setColumnWidth(i, 250)

            # Select the first row after loading the data
            if self.data_table.rowCount() > 0:
                self.data_table.setCurrentCell(0, 0)  # Select the first cell

            self.update_status_labels()
            # Call load_attached_documents only if there's a selection
            if self.data_table.currentRow() >= 0:
                self.load_attached_documents()


        def transform_data(self, file_path, output):
            try:
                # Open and read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)

                    # Check if required columns are present in the file
                    required_columns = ['anteriore', 'posteriore', 'contemporaneo', 'properties_ant', 'properties_post']
                    for column in required_columns:
                        if column not in header:
                            raise ValueError(f"Column {column} not present in the file.")

                    # Get column indices
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



                    # If a required value is not present, raise an exception
                    required_values = [col1_values, col2_values, col3_values, col4_values, col5_values]
                    for val in required_values:
                        if not val:
                            raise ValueError("Requested value not present.")

                    new_col = []
                    for val1 in col1_values:
                        if val1:
                            for r in all_rows:
                                if r[0] == val1:
                                    new_col.append(['anteriore', val1, r[1], r[3], r[4], r[5]])

                    for val2 in col2_values:
                        if val2:
                            for r in all_rows:
                                if r[0] == val2:
                                    new_col.append(['posteriore', val2, r[1], r[3], r[4], r[5]])

                    for val3 in col3_values:
                        if val3:
                            for r in all_rows:
                                if r[0] == val3:
                                    new_col.append(['contemporaneo', val3, r[1], r[3], r[4], r[5]])

                    for val4 in col4_values:
                        if val4:
                            for r in all_rows:
                                if r[0] == val4:
                                    new_col.append(['properties_ant', val4, r[1], r[3], r[4], r[5]])

                    for val5 in col5_values:
                        if val5:
                            for r in all_rows:
                                if r[0] == val5:
                                    new_col.append(['properties_post', val5, r[1], r[3], r[4], r[5]])


                    row += [new_col]
                    rows.append(row)

                #Apri e scrivi nel file di output
                with open(output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_header)
                    for row in rows:
                        writer.writerow(row[:-1] + [' '.join([str(e) for e in row[-1]])])

                self.check_consistency(output, 'log/log.txt')
                self.show_errors_in_dock_widget('log/log.txt')

            except IOError:
                self.show_error('Error reading or writing the file.')
            except ValueError as ve:
                self.show_error(str(ve))
            except Exception as e:
                self.show_error(f"Unknown error:{e}")
        def transform_data_google(self,file_buffer, output_buffer):
            # Leggi le righe dal buffer StringIO
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

            # Write the transformed data to the output buffer
            output_buffer.seek(0)
            print(output_buffer)
            writer = csv.writer(output_buffer)
            writer.writerow(new_header)
            for row in rows:
                writer.writerow(row[:-1] + [' '.join([str(e) for e in row[-1]])])

        def on_convert_data_pressed(self):
            try:
                data_list, id_us_dict = self.read_transformed_csv(self.data_file)
                CSVMapper.GRAPHML_PATH, _ = QFileDialog.getSaveFileName(self, 'Select the folder and file name',
                                                                        '', 'Graphml Files (*.graphml)')

                if not CSVMapper.GRAPHML_PATH:
                    self.show_error('No file selected.')
                    return

                # Get directory and base path
                base_path, _ = os.path.splitext(CSVMapper.GRAPHML_PATH)
                dir_path = os.path.dirname(base_path)

                config.path = dir_path  # Set config.path
                print(f"Config path setted in: {config.path}")

                dlg = pyarchinit_Interactive_Matrix(data_list, id_us_dict)
                dlg.generate_matrix()  # Crea il file .dot

                dot_file_path = os.path.join(config.path, "Harris_matrix2ED.dot")  # Percorso completo al file dot

                # Wait for the .dot file to be created, with a timeout
                timeout = 10
                start_time = time.time()

                while not os.path.exists(dot_file_path):
                    if time.time() - start_time > timeout:
                        raise Exception("Timeout while waiting for .dot file to be created.")
                    time.sleep(1)  # Wait for one second
                '''
                dottoxml = os.path.join('parser', 'dottoxml.py')
                print(dottoxml)
                # Create the path to the new dot file
                dot_file = os.path.join(dir_path, "Harris_matrix2ED.dot")
                print(dot_file)
    
                python_command = 'python3' if sys.platform != 'win32' else 'python'
                print(python_command)
    
                # Handle subprocess error
                try:
                    print()
                    subprocess.check_call([python_command, dottoxml, '-f', 'Graphml', dot_file, CSVMapper.GRAPHML_PATH],
                                          shell=True)
                except subprocess.CalledProcessError as e:
                    raise Exception("Error during subprocess call: " + str(e))
                '''
                dottoxml = os.path.join('parser', 'dottoxml.py')
                print(dottoxml)

                dot_file = os.path.join(dir_path, "Harris_matrix2ED.dot")
                print(dot_file)

                python_command = 'python3' if sys.platform != 'win32' else 'python'
                print(python_command)

                # Assicurati che i file esistano
                if not os.path.exists(dottoxml) or not os.path.exists(dot_file):
                    raise Exception("File not found")

                # Esecuzione del comando
                try:
                    command = [python_command, dottoxml, '-f', 'Graphml', dot_file, CSVMapper.GRAPHML_PATH]
                    print("Execution of the command:", " ".join(command))

                    # Utilizza 'shell=False' e passa il comando come lista
                    subprocess.check_call(command, shell=False)
                except subprocess.CalledProcessError as e:
                    print("Error executing subprocess:")
                    print("Return code:", e.returncode)
                    raise

                with open(CSVMapper.GRAPHML_PATH, 'r') as file:
                    filedata = file.read()

                # Replace the target string
                filedata = filedata.replace("b'", '')
                filedata = filedata.replace("graphml>'", 'graphml>')

                # Write the file out again
                with open(CSVMapper.GRAPHML_PATH, 'w') as file:
                    file.write(filedata)
                self.show_message('Conversion completed successfully.')
                self.d_graph()
            except IOError:
                self.show_error('Error reading or writing the file.')
            except KeyError as e:
                self.show_error('Error: ' + str(e))
            except Exception as e:
                self.show_error('Unknown error: ' + str(e))



        def read_transformed_csv(self, file_path):
            data_list = []
            id_us_dict = {}

            try:
                with open(file_path, "r") as f:
                    reader = csv.reader(f)
                    header = next(reader)

                    # Check if required columns are present in the file
                    required_columns = ["nome us", "tipo", "descrizione", "epoca", "epoca index", "rapporti"]
                    for column in required_columns:
                        if column not in header:
                            raise ValueError(f"Column {column} not present in the file.")

                    # Find the indices of the desired columns
                    us_idx = header.index("nome us")
                    unita_tipo_idx = header.index("tipo")
                    descrizione_idx = header.index("descrizione")
                    epoca_idx = header.index("epoca")
                    e_idx = header.index("epoca index")
                    rapporti_idx = header.index("rapporti")

                    # Read and parse each row
                    for row in reader:
                        # Extract the values from the desired columns
                        us = row[us_idx]
                        unita_tipo = row[unita_tipo_idx]
                        descrizione = row[descrizione_idx]
                        epoca = row[epoca_idx]
                        e_id = row[e_idx]
                        rapporti_stratigrafici = row[rapporti_idx]

                        # Add the values to data_list and id_us_dict
                        data_list.append([us, unita_tipo, descrizione, epoca, e_id, rapporti_stratigrafici])
                        id_us_dict[us] = {"nome us": us}

            except IOError:
                self.show_error('Error reading the file.')
            except ValueError as ve:
                self.show_error(str(ve))
            except Exception as e:
                self.show_error(f"Unknown error: {e}")

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
                            inverse_relation_type = 'properties_post'
                        elif relation_type == 'properties_post':
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
                                f"Error: Inconsistent relation between{us_name} ({relation_type}) and {related_us} ({inverse_relation_type}).")

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

        def on_pushButton_addtab_pressed(self):
            new_row_index = self.insert_new_row('tableWidget_relationship')
            self.tablewidget_change_value(new_row_index)  # Update only the new row

        def on_pushButton_removetab_pressed(self):
            # Get the currently selected row in tableWidget_relationship
            selected_row = self.tableWidget_relationship.currentRow()
            if selected_row == -1:
                print("No row selected.")
                return

            # Assuming the first column of tableWidget_relationship contains 'nameus'
            nameus_item = self.tableWidget_relationship.item(selected_row, 1)
            if not nameus_item:
                print("No 'nameus' found for the selected row.")
                return
            nameus = nameus_item.text()

            # Remove the corresponding row from self.data_table
            self.remove_or_update_data_table(nameus)

            # Remove the selected row from tableWidget_relationship
            self.tableWidget_relationship.removeRow(selected_row)

            # Refresh the data_table UI
            self.refresh_data_table()
            self.update_status_labels()
            print(f"Removed tab with 'nameus': {nameus}")
            self.remove_row('tableWidget_relationship')
        def insert_new_row(self, table_widget_name):

            # Mappatura dei termini italiani in inglese
            italian_to_english = {
                "anteriore": "anterior",
                "posteriore": "posterior",
                "contemporaneo": "contemporary",
                "properties_ant": "properties_ant",
                "properties_post": "properties_post"
            }

            # Valori italiani originali
            valuesRS = ["anteriore", "posteriore", "contemporaneo", "properties_ant", "properties_post"]

            # Translate Italian values to English using the mapping
            valuesRS_english = [italian_to_english[item] for item in valuesRS]

            # Configura ComboBoxDelegate con valori inglesi
            self.delegateRS = ComboBoxDelegate()
            self.delegateRS.def_values(valuesRS_english)
            self.delegateRS.def_editable('False')
            self.tableWidget_relationship.setItemDelegateForColumn(0, self.delegateRS)

            # Leggere valori da file CSV
            typeunit_df = pd.read_csv(os.path.join('template', 'unita_tipo.csv'))
            epoch_df = pd.read_csv(os.path.join('template', 'epoche_storiche.csv'))

            # Estrai i valori per i QComboBox
            value2 = typeunit_df['TIPO'].tolist()
            value3 = [f"{row['Periodo']} - {row['Evento']}" for _, row in epoch_df.iterrows()]

            # Configura i delegati con i valori di CSV
            self.delegateRS2 = ComboBoxDelegate()
            self.delegateRS2.def_values(value2)
            self.delegateRS2.def_editable('True')
            self.tableWidget_relationship.setItemDelegateForColumn(2, self.delegateRS2)

            self.delegateRS3 = ComboBoxDelegate()
            self.delegateRS3.def_values(value3)
            self.delegateRS3.def_editable('True')
            self.tableWidget_relationship.setItemDelegateForColumn(4, self.delegateRS3)

            table_widget = getattr(self, table_widget_name)
            row_position = table_widget.rowCount()

            table_widget.insertRow(row_position)

            return row_position

        def remove_row(self, table_name):
            table = getattr(self, table_name)

            table_row_count = table.rowCount()
            rowSelected = table.selectedIndexes()

            # Controlla se la selezione non è vuota
            if rowSelected:
                rowIndex = rowSelected[0].row()
                table.removeRow(rowIndex)

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data
        print(self._data)

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

    app.setStyle('Fusion')
    mapper = CSVMapper()
    mapper.show()
    app.exec_()
