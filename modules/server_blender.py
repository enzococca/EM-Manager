import bpy
import socket
import threading

def handle_client(client_socket):
    """
    Gestisce le connessioni in arrivo dal client.
    """
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if request:
                exec(request)  # Esegui il comando ricevuto
                client_socket.send(b'Command executed')
            else:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9000))
    server.listen(5)
    print("Server started on port 9000...")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Avvia il server in un thread separato per non bloccare Blender
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()
print(server_thread)