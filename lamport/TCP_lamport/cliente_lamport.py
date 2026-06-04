import socket
import threading
import time

"""codigo limpio"""


"""Clase """
class LamportClient:
    def __init__(self, server_ip, server_port=5000):
        self.lc = 0
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((server_ip, server_port))
        print("Conectado al servidor Lamport")

    def send_message(self, message):
        self.lc += 1
        data = f"{self.lc}:{message}"
        self.client.send(data.encode())
        print(f"[{self.lc}] Enviado: {message}")

    def receive(self):
        while True:
            try:
                data = self.client.recv(1024).decode()
                if data:
                    received_lc, msg = map(int, data.split(':', 1)) if ':' in data else (0, data)
                    self.lc = max(self.lc, received_lc) + 1
                    print(f"[{self.lc}] Recibido: {msg}")
            except:
                break

if __name__ == "__main__":
    client = LamportClient("192.168.1.10")  # IP del servidor
    threading.Thread(target=client.receive, daemon=True).start()
    
    while True:
        msg = input("Mensaje: ")
        if msg.lower() == 'exit':
            break
        client.send_message(msg)