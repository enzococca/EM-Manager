import os
import platform
import subprocess
from PyQt5.QtWidgets import QMessageBox
def is_graphviz_installed():
    try:
        subprocess.run(["dot", "-V"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def is_graphviz_in_path():
    path = os.getenv('PATH') or os.getenv('Path')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, "bin")
        if os.path.exists(p) and os.access(p, os.X_OK):
            return True
    return False

def install_graphviz():
    if platform.system() == 'Darwin':  # macOS
        QMessageBox.warning(None,'Graphviz',"Graphviz non è installato.\n "
                                            "Se non installi Graphviz non puoi convertire.\n"
                                            "Puoi installarlo tramite Homebrew con il comando: 'brew install graphviz'")
    else:
        QMessageBox.warning(None,'Graphviz',"Graphviz non è installato.\n "
                                            "Se non installi Graphviz non puoi convertire.\n"
                                            "Puoi installarlo seguendo le istruzioni sul sito ufficiale: https://graphviz.org/download/")

def set_graphviz_path():
    QMessageBox.warning(None,'Variabile di ambiente',"Graphviz non è nel PATH.\n Aggiungi la directory di Graphviz al PATH del tuo sistema operativo.")

def check_graphviz(message):
    if not is_graphviz_installed():
        install_graphviz()
        return
    if not is_graphviz_in_path():
        set_graphviz_path()
        return
    message.showMessage("Graphviz è installato e pronto all'uso.")