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

        # Get the value from the first column of the selected row
        nameus_item = self.main_window.data_table.item(selected_row, 0)
        if not nameus_item:
            print("No 'nameus' found for the selected row.")
            return
        nameus = nameus_item.text()

        # Check the value of the second column
        type_item = self.main_window.data_table.item(selected_row, 1)
        if type_item and type_item.text().lower() in ['property', 'document', 'combiner', 'extractor']:
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                new_file_name = f"{nameus}{os.path.splitext(file_path)[1]}"  # Keep the original extension

                # Construct the path to the "DosCo" folder relative to the project's CSV file path
                dosco_folder = os.path.join(os.path.dirname(self.main_window.data_file), "DosCo")
                if not os.path.exists(dosco_folder):
                    os.makedirs(dosco_folder)
                new_file_path = os.path.join(dosco_folder, new_file_name)

                # Copy and rename the file to the "DosCo" folder
                shutil.copy(file_path, new_file_path)

                # Add the new file name (not path) to the QListWidget
                self.addItem(new_file_name)
        else:
            print("The selected row's type is not allowed for media association.")
