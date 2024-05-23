import sys
import socket
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QListWidget, QMessageBox, QDialog


class BlenderCommandWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Blender Commands')
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()

        self.command_list = QListWidget()
        self.command_list.itemSelectionChanged.connect(self.show_command_help)
        self.layout.addWidget(self.command_list)

        self.args_label = QLabel('Enter Arguments (separated by commas):')
        self.layout.addWidget(self.args_label)

        self.args_input = QLineEdit()
        self.layout.addWidget(self.args_input)

        self.send_button = QPushButton('Send Command')
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

        self.response_label = QLabel('Response:')
        self.layout.addWidget(self.response_label)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.layout.addWidget(self.response_output)

        self.help_label = QLabel('Command Help:')
        self.layout.addWidget(self.help_label)

        self.command_help = QTextEdit()
        self.command_help.setReadOnly(True)
        self.layout.addWidget(self.command_help)

        self.setLayout(self.layout)

        # Popola dinamicamente la lista dei comandi
        self.populate_command_list()

    def populate_command_list(self):
        commands = self.get_commands_from_server()
        if commands:
            for command in commands:
                self.command_list.addItem(command['name'])
                self.command_help.append(f"{command['name']}: {command['description']}")
        else:
            self.command_list.addItem('No commands available')

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

    def show_command_help(self):
        selected_command = self.command_list.currentItem().text()
        commands = self.get_commands_from_server()
        for command in commands:
            if command['name'] == selected_command:
                self.command_help.setText(f"{command['name']}: {command['description']}")
                break

    def send_command(self):
        command = self.command_list.currentItem().text()
        args = self.args_input.text().split(',')
        response = self.send_to_server(command, args)
        self.response_output.setText(response)

    def send_to_server(self, command, args):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 9001))  # Assicurarsi che questa porta sia corretta
            command_with_args = f"{command} {' '.join(map(str, args))}"
            client.send(command_with_args.encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
            client.close()
            return response
        except Exception as e:
            return f"Error: {e}"