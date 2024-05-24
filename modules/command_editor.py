import re
import sys
import socket
import json
import textwrap
import time

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QListWidget, QMessageBox, QHBoxLayout)

class CommandEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Command Editor')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.command_list = QListWidget()
        self.command_list.itemSelectionChanged.connect(self.load_command)
        self.layout.addWidget(self.command_list)

        self.command_label = QLabel('Enter Command Name:')
        self.layout.addWidget(self.command_label)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("e.g., Export Mesh")
        self.layout.addWidget(self.command_input)

        self.function_label = QLabel('Enter Function Code:')
        self.layout.addWidget(self.function_label)

        self.function_input = QTextEdit()
        self.function_input.setPlaceholderText("""e.g., 
def export_proxies(export_path):
    \"\"\"
    Export the proxies from Blender to a specified folder.
    \"\"\"
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.export_scene.obj(filepath=os.path.join(export_path, f"{obj.name}_proxy.obj"))
            obj.select_set(False)
    print(f"Proxies exported to {export_path}")
    return "Proxies exported"
                                                """)
        self.layout.addWidget(self.function_input)

        self.save_button = QPushButton('Save Command')
        self.save_button.clicked.connect(self.save_command)
        self.layout.addWidget(self.save_button)

        self.update_button = QPushButton('Update Command')
        self.update_button.clicked.connect(self.update_command)
        self.layout.addWidget(self.update_button)

        self.delete_button = QPushButton('Delete Command')
        self.delete_button.clicked.connect(self.delete_command)
        self.layout.addWidget(self.delete_button)

        self.response_label = QLabel('Response:')
        self.layout.addWidget(self.response_label)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.layout.addWidget(self.response_output)

        self.load_command_list()

    def load_command_list(self):
        self.command_list.clear()
        commands = self.get_commands_from_server()
        print(commands)
        if commands:

            self.command_list.addItems([cmd['name'] for cmd in commands])
        else:
            self.command_list.addItem('No commands available')
        self.command_list.setCurrentRow(0)  # Imposta il primo elemento come l'elemento corrente

        self.command_list.update()
    def get_commands_from_server(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 9001))  # Assicurarsi che questa porta sia corretta
            client.send(b'GET_COMMANDS')
            response = client.recv(4096).decode('utf-8')
            client.close()
            return json.loads(response)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to get commands: {e}')
            return []

    def load_command(self):
        selected_command = self.command_list.currentItem().text()
        commands = self.get_commands_from_server()
        for command in commands:
            if command['name'] == selected_command:
                self.command_input.setText(command['name'])
                self.function_input.setText(command['code'])
                break

    def save_command(self):
        command_name = self.command_input.text()
        function_code = self.function_input.toPlainText()

        if command_name and function_code:
            try:
                self.append_to_client_file(command_name, function_code)
                QMessageBox.information(self, 'Success', 'Command saved successfully')
                self.load_command_list()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save command: {e}')
        else:
            QMessageBox.warning(self, 'Warning', 'Command name and function code cannot be empty')

    def update_command(self):
        command_name = self.command_input.text()
        function_code = self.function_input.toPlainText()

        if command_name and function_code:
            try:
                self.update_client_file(command_name, function_code)
                QMessageBox.information(self, 'Success', 'Command updated successfully')
                self.load_command_list()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to update command: {e}')
        else:
            QMessageBox.warning(self, 'Warning', 'Command name and function code cannot be empty')

    def delete_command(self):
        command_name = self.command_input.text()

        if command_name:
            try:
                deleted = self.delete_from_client_file(command_name)
                if deleted:
                    QMessageBox.information(self, 'Success', 'Command deleted successfully')

                    self.load_command_list()

                    self.command_input.clear()
                    self.function_input.clear()
                    self.repaint()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to delete command: {e}')
        else:
            QMessageBox.warning(self, 'Warning', 'Command name cannot be empty')
    def append_to_client_file(self, command_name, function_code):
        client_file_path = 'modules/client_blender.py'

        # Estrae il nome della funzione dal codice della funzione
        function_name = re.findall(r'def (\w+)\(', function_code)[0]

        # Estrae la descrizione della funzione
        description_match = re.search(r'""".*?\n\s*(.*?)\n.*?"""', function_code, re.DOTALL)
        description = description_match.group(1).strip() if description_match else "No description provided"

        # Formatta correttamente il codice della funzione
        formatted_function_code = textwrap.dedent(function_code).strip()

        function_code_with_decorator = f"""
        {formatted_function_code}

                """

        register_code = f"""
        register_command("{command_name}", {function_name}, "{description}", """ + '"""' + f"""{formatted_function_code}""" + '"""' + """)
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

    def update_client_file(self, command_name, function_code):
        self.delete_from_client_file(command_name)
        self.append_to_client_file(command_name, function_code)

    def delete_from_client_file(self, command_name):
        client_file_path = 'modules/client_blender.py'

        with open(client_file_path, 'r') as file:
            content = file.read()

        function_name_match = re.search(rf'register_command\("{command_name}", (\w+),', content)

        if function_name_match:
            function_name = function_name_match.group(1)

            # New regex pattern
            pattern = rf'def {function_name}\(.*?def'
            pattern_register = rf'register_command\("{command_name}",.*?"""\)'

            content = self.find_and_remove_register(function_name, content, pattern_register)
            content = self.find_and_remove_function(function_name, content, pattern)

            with open(client_file_path, 'w') as file:
                file.write(content)
                return True
        else:
            print(f"Command {command_name} not found.")
            return False

    def find_and_remove_function(self, function_name, content, pattern):
        # Replace the function definition from "def function_name(parameters):" to the next "def"
        # It doesn't remove the last "def" included in the regex, that's why the slicing [: -3]
        function_pattern = re.compile(pattern, re.DOTALL)
        new_content = re.sub(function_pattern, 'def', content)[:-3]
        return new_content
    def find_and_remove_register(self, function_name, content, pattern):
        # Compile the regex pattern and use it to replace matched content with an empty string
        function_pattern = re.compile(pattern, re.DOTALL)
        new_content = re.sub(function_pattern, '', content)
        return new_content

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = CommandEditor()
    editor.show()
    sys.exit(app.exec_())
