import os
import socket
import threading
from cryptography.fernet import Fernet

# === ENCRYPTION KEY CONFIGURATION ===
KEY_FILE = "encryption_key.key"

def load_or_create_key():
    """
    Creates a new key if it doesn't exist, or loads it from the file.
    """
    if not os.path.exists(KEY_FILE):
        # Generate new key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        print(f"[Info] Key generated and saved in '{KEY_FILE}'")
    else:
        # Load key from the file
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
        print(f"[Info] Key loaded from '{KEY_FILE}'")
    return key

# Load or generate the key
KEY = load_or_create_key()
CIPHER = Fernet(KEY)

# === SERVER ===
clients = []  # List of connected clients

def start_server(host, port):
    """
    Starts the server that listens to multiple clients and manages them simultaneously.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[Server] Listening on {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[Server] Client connected from {addr}")
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket,)).start()

def handle_client(client_socket):
    """
    Handles communication with a connected client.
    """
    while True:
        try:
            # Receive and decrypt the message
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = CIPHER.decrypt(encrypted_message).decode()
            print(f"[Client] {message}")

            # Broadcast the message to all clients
            broadcast_message(message, client_socket)
        except Exception as e:
            print(f"[Error] {e}")
            break

    # Remove the client from the list and close the connection
    clients.remove(client_socket)
    client_socket.close()

def broadcast_message(message, sender_socket):
    """
    Sends a message to all clients except the sender.
    """
    encrypted_message = CIPHER.encrypt(message.encode())
    for client in clients:
        if client != sender_socket:
            try:
                client.send(encrypted_message)
            except:
                clients.remove(client)

# === CLIENT ===
def start_client(host, port):
    """
    Starts a client that connects to the server and sends/receives messages.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"[Client] Connected to {host}:{port}...")

    threading.Thread(target=receive_messages, args=(client_socket,)).start()

    while True:
        try:
            message = input("[You]: ")
            encrypted_message = CIPHER.encrypt(message.encode())
            client_socket.send(encrypted_message)
        except KeyboardInterrupt:
            break

def receive_messages(client_socket):
    """
    Receives messages from the server and decrypts them.
    """
    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = CIPHER.decrypt(encrypted_message).decode()
            print(f"[Server]: {message}")
        except Exception as e:
            print(f"[Error] {e}")
            break
        
# === MENÚ PRINCIPAL ===
if __name__ == "__main__":
    print("=== Chat Encriptado ===")
    mode = input("Selecciona el modo (servidor/cliente): ").strip().lower()

    if mode == "servidor":
        host = input("Ingresa la dirección IP del servidor (0.0.0.0 para todas): ").strip()
        port = int(input("Ingresa el puerto: ").strip())
        start_server(host, port)

    elif mode == "cliente":
        host = input("Ingresa la dirección IP del servidor: ").strip()
        port = int(input("Ingresa el puerto del servidor: ").strip())
        start_client(host, port)

    else:
        print("[Error] Modo no válido.")
