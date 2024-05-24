import socket
import os
import threading
import bpy
import json

# Dizionario per memorizzare i comandi e le rispettive funzioni
commands = {}
command_descriptions = {}
command_codes = {}

def register_command(command_name, func, description, code):
    """
    Registra un nuovo comando.

    Parameters:
    command_name (str): Il nome del comando.
    func (callable): La funzione che esegue il comando.
    description (str): La descrizione del comando e i suoi argomenti.
    code (str): Il codice della funzione.
    """
    commands[command_name] = func
    command_descriptions[command_name] = description
    command_codes[command_name] = code

def get_commands():
    """
    Restituisce la lista dei comandi registrati con le descrizioni e i codici.
    """
    return [{"name": name, "description": command_descriptions[name], "code": command_codes[name]} for name in commands]

def handle_client(client_socket):
    """
    Gestisce le connessioni in arrivo dal server Blender e esegue i comandi.
    """
    try:
        while True:
            request = client_socket.recv(4096).decode('utf-8')
            if request:
                print(f"Received command: {request}")
                parts = request.split()
                command = parts[0]
                args = parts[1:]

                if command == "GET_COMMANDS":
                    response = json.dumps(get_commands())
                    client_socket.send(response.encode('utf-8'))
                elif command in commands:
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



# Comandi personalizzati
# <CUSTOM_COMMANDS>



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



def add_cube(size, x, y, z):
    """
    Aggiunge un cubo alla scena di Blender.
    """
    sizes = float(size)
    location = (float(x), float(y), float(z))
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.mesh.primitive_cube_add(size=sizes, location=location)
    print(f"Cube added at {location} with size {size}")
    return "Cube added"









# </CUSTOM_COMMANDS>




register_command("ADD_CUBE", add_cube, "ADD_CUBE: size, x, y, z - Aggiunge un cubo alla scena di Blender.", """def add_cube(size, x, y, z):
    \"""
    Aggiunge un cubo alla scena di Blender.
    \"""
    size = float(size)
    location = (float(x), float(y), float(z))
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    print(f"Cube added at {location} with size {size}")
    return "Cube added"
""")

register_command("EXPORT_PROXY", export_proxies, "EXPORT_PROXY: export_path - Esporta i proxy di Blender in una cartella specificata.", """def export_proxies(export_path):
    \"""
    Esporta i proxy di Blender in una cartella specificata.
    \"""
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj  # Set active object to the current one
            bpy.ops.wm.obj_export(context_override, filepath=os.path.join(export_path, f"{obj.name}_proxy.obj"), use_selection=True)
            obj.select_set(False)
    print(f"Proxies exported to {export_path}")
    return "Proxies exported"
""")




# Avvia il client esterno
start_client()






