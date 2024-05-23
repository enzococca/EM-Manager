import re
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
import socket

class CommandEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Command Editor')
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.command_label = QLabel('Enter Command Name:')
        self.layout.addWidget(self.command_label)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("es: Export Mesh")
        self.layout.addWidget(self.command_input)

        self.function_label = QLabel('Enter Function Code:')
        self.layout.addWidget(self.function_label)

        self.function_input = QTextEdit()
        self.function_input.setPlaceholderText("""es.: 
def export_proxies(export_path):

    #Export the proxies from Blender to a specified folder.

    if not os.path.exists(export_path):
        os.makedirs(export_path)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.export_scene.obj(filepath=os.path.join(export_path, f"{obj.name}_proxy.obj"))
            obj.select_set(False)
    print(f"Proxies exported to {export_path}")
    return "Proxies exported"")
                                                """)
        self.layout.addWidget(self.function_input)

        self.send_button = QPushButton('Send Command')
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

        self.save_button = QPushButton('Save Command')
        self.save_button.clicked.connect(self.save_command)
        self.layout.addWidget(self.save_button)

        self.response_label = QLabel('Response:')
        self.layout.addWidget(self.response_label)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.layout.addWidget(self.response_output)

    def send_command(self):
        command = self.command_input.text()
        if command:
            response = self.send_to_server(command)
            self.response_output.setText(response)
        else:
            QMessageBox.warning(self, 'Warning', 'Command cannot be empty')

    def send_to_server(self, command):
        try:

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 9001))  # Connect to the server socket
            client.send(command.encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
            client.close()
            return response
        except Exception as e:
            return f"Error: {e}"

    def save_command(self):
        command_name = self.command_input.text()
        function_code = self.function_input.toPlainText()

        if command_name and function_code:
            try:
                self.append_to_client_file(command_name, function_code)
                QMessageBox.information(self, 'Success', 'Command saved successfully')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save command: {e}')
        else:
            QMessageBox.warning(self, 'Warning', 'Command name and function code cannot be empty')

    import re

    def append_to_client_file(self, command_name, function_code):
        client_file_path = 'client_blender.py'

        # Estrae il nome della funzione dal codice della funzione
        function_name = re.findall(r'def (\w+)\(', function_code)[0]

        # Estrae la descrizione della funzione
        description_match = re.search(r'""".*?\n\s*(.*?)\n.*?"""', function_code, re.DOTALL)
        description = description_match.group(1).strip() if description_match else "No description provided"

        function_code_with_decorator = f"""
{function_code}

        """

        register_code = f"""
register_command("{command_name}", {function_name}, "{description}")
        """

        with open(client_file_path, 'r') as file:
            content = file.read()

        new_content = content.replace('# <CUSTOM_COMMANDS>\n',
                                      f'# <CUSTOM_COMMANDS>\n{function_code_with_decorator}\n')

        with open(client_file_path, 'w') as file:
            file.write(new_content)

        new_register = new_content.replace('# </CUSTOM_COMMANDS>\n',
                                           f'# </CUSTOM_COMMANDS>\n{register_code}\n')

        with open(client_file_path, 'w') as file:
            file.write(new_register)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = CommandEditor()
    editor.show()
    sys.exit(app.exec_())
