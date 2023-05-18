import os,sys,winreg
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
    path = os.getenv('Path', os.getenv('PATH'))
    for p in path.split(os.path.pathsep):
        if sys.platform == 'win32':
            dot_path = os.path.join(p, "dot.exe")
        else:
            dot_path = os.path.join(p, "dot")
        if os.path.exists(dot_path) and os.access(dot_path, os.X_OK):
            return True
    return False


def install_graphviz():
    if platform.system() == 'Darwin':  # macOS
        QMessageBox.warning(None,'Graphviz',"Graphviz non è installato.\n "
                                            "Se non installi Graphviz non puoi convertire.\n"
                                            "Puoi installarlo tramite Homebrew con il comando: 'brew install graphviz'\n"
                                            "Dopo, sempre dal terminale avvia questo comando: export PATH='${PATH}:/usr/local/bin'\n"
                                            "Questo ti consete di inserire graphviz nella variabile di ambiente")
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
    if platform.system() == 'win32':
        # Aggiungi la directory di Graphviz al PATH sulla piattaforma Windows
        graphviz_folder = "C:\\Program Files\\Graphviz\\bin"
        with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as reg:
            with winreg.OpenKeyEx(reg, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', access=winreg.KEY_WRITE) as key:
                path, _ = winreg.QueryValueEx(key, "Path")
                if not graphviz_folder in path:
                    path += ";" + graphviz_folder
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, path)

        # Verifica se Graphviz può essere trovato nel PATH aggiornato
        if not is_graphviz_in_path():
            QMessageBox.warning(None,'Variabile di ambiente',"Impossibile trovare Graphviz nella variabile PATH.\n Assicurati che il percorso di installazione di Graphviz sia stato aggiunto alla variabile d'ambiente PATH.")
    elif platform.system() == 'Darwin':
        # Aggiungi la directory di Graphviz al PATH sulla piattaforma macOS
        graphviz_folder = "/usr/local/bin"
        os.environ["PATH"] += os.pathsep + graphviz_folder
    else:
        # Aggiungi la directory di Graphviz al PATH sulla piattaforma Linux
        graphviz_folder = "/usr/bin/dot"
        os.environ["PATH"] += os.pathsep + graphviz_folder

        # Verifica se Graphviz può essere trovato nel PATH aggiornato
        if not is_graphviz_in_path():
            QMessageBox.warning(None,'Variabile di ambiente',"Impossibile trovare Graphviz nella variabile PATH.\n Assicurati che il percorso di installazione di Graphviz sia stato aggiunto alla variabile d'ambiente PATH.")

def check_graphviz(message):
    if not is_graphviz_installed():
        install_graphviz()
        message.showMessage("Graphviz è installato")
        return
    if not is_graphviz_in_path():
        set_graphviz_path()
        message.showMessage("Graphviz non è nella  variabile d'ambinete")

        return

    message.showMessage("Graphviz è installato e pronto all'uso.")