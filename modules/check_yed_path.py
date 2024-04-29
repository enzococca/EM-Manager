import os
import webbrowser
import platform

class YEdSetup:
    def __init__(self):
        # Definisce i percorsi previsti per yEd su Windows e macOS
        self.yed_paths = {
            'Windows': "C:/Program Files/yWorks/yEd/yEd.exe",
            'Darwin': "/Applications/yEd.app/Contents/MacOS/yEd"  # Percorso del binario yEd all'interno del bundle dell'app
        }
        self.download_url = "https://www.yworks.com/products/yed/download"

    def get_yed_path(self):
        # Rileva il sistema operativo
        current_platform = platform.system()

        # Restituisce il percorso a yEd se esiste, altrimenti None
        return self.yed_paths.get(current_platform) if current_platform in self.yed_paths else None

    def check_installation(self):
        yed_path = self.get_yed_path()
        if yed_path and os.path.exists(yed_path):
            print("yEd is already installed.")
            return yed_path
        else:
            print("yEd is not installed. Opening download page...")
            webbrowser.open(self.download_url)
            input("Please download and install yEd from the opened web page. Press Enter once yEd is installed.")
            return None

# Come usarlo:
# if __name__ == "__main__":
#     yed_setup = YEdSetup()
#     yed_path = yed_setup.check_installation()
#     if yed_path:
#         print(f"yEd is installed at {yed_path}")
#     else:
#         print("Please install yEd before continuing.")
