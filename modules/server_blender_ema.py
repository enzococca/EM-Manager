import socket

def send_command_to_blender(command, host='localhost', port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.sendall(command.encode('utf-8'))
        response = sock.recv(1024)
        print("Risposta da Blender:", response.decode('utf-8'))
    finally:
        sock.close()

# Invia un comando di test al server Blender
send_command_to_blender("run_function")