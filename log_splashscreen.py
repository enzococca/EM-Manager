from PyQt5 import QtCore, QtGui, QtWidgets

class LogDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.logo_label = QtWidgets.QLabel(self)
        self.logo_label.setPixmap(QtGui.QPixmap("splash_logo.png"))
        self.layout.addWidget(self.logo_label)
        self.log_edit = QtWidgets.QPlainTextEdit(self)
        self.log_edit.setReadOnly(True)
        self.layout.addWidget(self.log_edit)
        self.resize(640, 480)
with open("temp.log", "r") as f:
    log_content = f.read()
log_dialog.log_edit.setPlainText(log_content)
app = QtWidgets.QApplication(sys.argv)
splash_pix = QtGui.QPixmap("splash_logo.png")
splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
splash.show()
QtWidgets.qApp.processEvents()

# Avvia la finestra di log con un breve ritardo
log_dialog = LogDialog()
QtCore.QTimer.singleShot(1000, log_dialog.show)

# Esegui il programma principale
main()

splash.finish(log_dialog)
sys.exit(app.exec_())
# Aggiorna lo splash screen
splash.showMessage("Elaborazione in corso...", QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)

# Scrivi sul log
log_dialog.log_edit.insertPlainText("Nuova riga di log\n")

# Aggiorna la finestra del log
QtWidgets.qApp.processEvents()


