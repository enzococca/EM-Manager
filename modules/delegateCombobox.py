
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QItemDelegate, QComboBox
class ComboBoxDelegate(QItemDelegate):
    values = ""
    editable = ""

    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)

    def def_values(self, values):
        self.values = values

    def def_editable(self, editable):
        self.editable = editable

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.values)
        editor.setEditable(eval(self.editable))
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole)  # .String()
        i = editor.findText(text)
        if i == -1:
            i = 0
        editor.setCurrentIndex(i)