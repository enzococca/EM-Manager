from PyQt5.QtWidgets import QSplashScreen, QApplication, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from EDMatrix2Graphml import CSVMapper
import sys

app = QApplication(sys.argv)

# Carica e ridimensiona l'immagine per lo splash screen
splash_pix = QPixmap('icon/EM2graphml_splash.png')
splash_pix = splash_pix.scaled(500, 500, Qt.KeepAspectRatio)  # Cambia le dimensioni qui

splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)

# Crea il layout per la finestra di log
log_layout = QVBoxLayout()

# Aggiungi un'etichetta per il titolo del log
# log_title = QLabel("Log:")
# log_title.setStyleSheet('font-size: 20px;')  # Cambia la dimensione del font qui
# log_layout.addWidget(log_title)

# Aggiungi un'etichetta per le righe del log
log_lines = QLabel()
log_lines.setStyleSheet(
    'background-color: rgba(255, 255, 255, 128); font-size: 18px;')  # Cambia la dimensione del font qui

# Aggiungi l'etichetta del contenuto del log al layout
log_layout.addWidget(log_lines)

# Crea il layout orizzontale e verticale per centrare il layout del log
hbox = QHBoxLayout()
vbox = QVBoxLayout()

# Aggiungi "stretch" su entrambi i lati del layout del log per centrarlo
hbox.addStretch(1)
hbox.addLayout(log_layout)
hbox.addStretch(1)

vbox.addStretch(1)
vbox.addLayout(hbox)
vbox.addStretch(1)

# Posiziona la finestra di log sopra l'immagine
splash.setLayout(vbox)

splash.show()

# Aggiungi righe al log
base_text = "Caricamento"
log_lines.setText(base_text)


def update_text():
    current_text = log_lines.text()
    if current_text.count('.') < 3:
        log_lines.setText(current_text + '.')
    else:
        log_lines.setText(base_text)


update_timer = QTimer()
# Aggiorna il testo ogni mezzo secondo
update_timer.timeout.connect(update_text)
update_timer.start(500)  # Aggiorna ogni mezzo secondo


def start_main():
    splash.close()
    update_timer.stop()  # Fermare il timer quando lo splash screen si chiude
    # Avvia il programma principale
    main_window = CSVMapper()
    main_window.show()


QTimer.singleShot(7000, start_main)

sys.exit(app.exec_())
