import os,sys
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
        if sys.platform == 'win32':
            bin_dir = os.path.join(p, "bin")
        else:
            bin_dir = p
        dot_path = os.path.join(bin_dir, "dot")
        if os.path.exists(dot_path) and os.access(dot_path, os.X_OK):
            return True
    return False

def install_graphviz():
    if platform.system() == 'Darwin':  # macOS
        QMessageBox.warning(None,'Graphviz',"Graphviz non è installato.\n "
                                            "Se non installi Graphviz non puoi convertire.\n"
                                            "Puoi installarlo tramite Homebrew con il comando: 'brew install graphviz'\n"
                                            "Dopo, sempre dal terminale avvia questo comando: export PATH='${PATH}:/usr/local/bin'\n"
                                            "Questo ti consetirà di inserire graphviz nella variabile di ambiente")
    elif platform.system() == 'Linux':
        distro = platform.linux_distribution(full_distribution_name=False)
        QMessageBox.warning(None,'Graphviz',"Graphviz non è installato.\n "
                                            "Se non installi Graphviz non puoi convertire.\n"
                                            f"Puoi installarlo sulla tua distribuzione {distro[0]} {distro[1]} tramite il gestore dei pacchetti della tua distribuzione (apt, dnf, pacman, etc.)")
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