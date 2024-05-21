# yed_automation.py
import pyautogui
import subprocess
import time


class YEdAutomation:
    def __init__(self, yed_path, graphml_path):
        self.yed_path = yed_path
        self.graphml_path = graphml_path

    def launch_yed(self):
        # Avvia yEd con il file GraphML
        subprocess.Popen([self.yed_path, self.graphml_path])
        time.sleep(10)  # Attendi che yEd si apra

    def bring_yed_to_foreground(self):
        # Tenta di trovare la finestra yEd e portarla in primo piano
        for _ in range(1):
            windows = pyautogui.getWindowsWithTitle("yEd")
            if windows:
                windows[0].activate()
                break
            time.sleep(1)
        else:
            raise RuntimeError("yEd window not found")

    def apply_swimlane_layout(self):
        # Premi Alt+Shift+S per applicare il layout Swimlane
        pyautogui.hotkey('alt', 'shift', 's')
        time.sleep(2)  # Attendi che il layout venga applicato
        # Premere "Invio" per confermare l'applicazione del layout
        pyautogui.press('enter')  # Si presuppone che il pulsante "OK" sia selezionato per impostazione predefinita
        time.sleep(2)  # Attendi che il layout venga applicato
    def save_file(self):
        # Premi Ctrl+S per salvare il file
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)  # Attendi il completamento dell'operazione di salvataggio

    def close_yed(self):
        # Chiudi yEd
        pyautogui.hotkey('alt', 'f4')


# # Come usarlo:

#     yed_path = yed_path
#     graphml_path = graphml_path
#
#     yed_auto = YEdAutomation(yed_path, graphml_path)
#     yed_auto.launch_yed()
#     yed_auto.bring_yed_to_foreground()
#     yed_auto.apply_swimlane_layout()
#     yed_auto.save_file()
#     yed_auto.close_yed()
