import socket
import os
import threading
import bpy


# Dizionario per memorizzare i comandi e le rispettive funzioni
commands = {}


def register_command(command_name, func):
    """
    Registra un nuovo comando.

    Parameters:
    command_name (str): Il nome del comando.
    func (callable): La funzione che esegue il comando.
    """
    commands[command_name] = func


def handle_client(client_socket):
    """
    Gestisce le connessioni in arrivo dal server Blender e esegue i comandi.
    """
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if request:
                print(f"Received command: {request}")
                command, *args = request.split()

                if command in commands:
                    response = commands[command](*args)
                    client_socket.send(response.encode('utf-8'))
                else:
                    client_socket.send(b'Unknown command')
            else:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()


def export_proxies(export_path):
    """
    Esporta i proxy di Blender in una cartella specificata.
    """
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.export_scene.obj(filepath=os.path.join(export_path, f"{obj.name}_proxy.obj"))
            obj.select_set(False)

    print(f"Proxies exported to {export_path}")
    return "Proxies exported"

def import_graphml(file_path):
    """
    Importa un file GraphML usando il plugin Extended Matrix Tool.
    """
    if os.path.exists(file_path):
        bpy.ops.import_mesh.graphml(filepath=file_path)  # Supponendo che il plugin abbia questa operazione
        print(f"GraphML file imported from {file_path}")
        return "GraphML imported"
    else:
        print(f"File {file_path} not found")
        return "File not found"


def import_json(file_path):
    """
    Importa un file JSON usando il plugin Extended Matrix Tool.
    """
    if os.path.exists(file_path):
        bpy.ops.import_scene.json(filepath=file_path)  # Supponendo che il plugin abbia questa operazione
        print(f"JSON file imported from {file_path}")
        return "JSON imported"
    else:
        print(f"File {file_path} not found")
        return "File not found"


def add_cube(size, x, y, z):
    """
    Aggiunge un cubo alla scena di Blender.
    """
    size = float(size)
    location = (float(x), float(y), float(z))
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    print(f"Cube added at {location} with size {size}")
    return "Cube added"


def start_client():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9001))
    server.listen(5)
    print("External client started on port 9001...")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


# Registrare i comandi
register_command("ADD_CUBE", add_cube)
register_command("EXPORT_PROXY", export_proxies)
register_command("IMPORT_GRAPHML", import_graphml)
register_command("IMPORT_JSON", import_json)
# </CUSTOM_COMMANDS>

    

    


    


# Avvia il client esterno
start_client()


