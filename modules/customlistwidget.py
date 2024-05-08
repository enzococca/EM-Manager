import shutil
import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem


class CustomListWidget(QListWidget):
    itemRemoved = pyqtSignal(QListWidgetItem)

    def __init__(self, parent=None):
        super(CustomListWidget, self).__init__(parent)
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.main_window = parent
    def removeSelectedItem(self):
        selected_item = self.currentItem()
        if selected_item:
            row = self.currentRow()
            self.itemRemoved.emit(selected_item)  # Emit the custom signal
            self.takeItem(row)  # Remove the item from the list


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # Get the selected item
            selected_item = self.currentItem()
            if selected_item:
                row = self.currentRow()
                self.itemRemoved.emit(selected_item)  # Emit the signal
                self.takeItem(row)  # Remove the item from the list
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        selected_row = self.main_window.data_table.currentRow()
        if selected_row == -1:
            print("No row selected.")
            return

        # Ottieni il valore dalla prima colonna della riga selezionata
        nameus_item = self.main_window.data_table.item(selected_row, 0)
        if not nameus_item:
            print("No 'nameus' found for the selected row.")
            return
        nameus = nameus_item.text()

        # Controlla il valore della seconda colonna
        type_item = self.main_window.data_table.item(selected_row, 1)
        if type_item and type_item.text().lower() in ['property', 'document', 'combiner', 'extractor']:
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                original_file_name = os.path.basename(file_path)
                file_extension = os.path.splitext(original_file_name)[1]  # Estrai l'estensione del file
                new_file_name = f"{nameus}_{original_file_name}"  # Costruisci il nuovo nome del file con nameus e il
                # nome del file originale

                # Costruisci il percorso della cartella "DosCo" relativo al percorso del file CSV del progetto
                dosco_folder = os.path.join(os.path.dirname(self.main_window.data_file), "DosCo")
                if not os.path.exists(dosco_folder):
                    os.makedirs(dosco_folder)
                new_file_path = os.path.join(dosco_folder, new_file_name)

                # Copia e rinomina il file nella cartella "DosCo".
                shutil.copy(file_path, new_file_path)

                # Aggiungi il nuovo nome file (non il percorso) al QListWidget
                self.addItem(new_file_name)
        else:
            print("The selected row's type is not allowed for media association.")
