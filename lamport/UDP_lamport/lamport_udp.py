import socket
import threading
import time

# ================= CONFIGURACIÓN =================
MY_IP = "192.168.1.12"          # Cambia esta IP en cada PC
MY_PORT = 5000

# Lista de todas las IPs de los participantes (incluyendo la tuya)
PEERS = [
    "192.168.1.10",
    "192.168.1.11",
    "192.168.1.12",
    "192.168.1.13",
    "192.168.1.14"
]

# ================================================

class LamportUDP:
    def __init__(self):
        self.lc = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((MY_IP, MY_PORT))
        print(f"✅ Lamport UDP iniciado en {MY_IP}:{MY_PORT} | LC = 0")

    def send_message(self, message):
        self.lc += 1
        data = f"{self.lc}:{message}:{MY_IP}"
        
        for peer in PEERS:
            if peer != MY_IP:
                try:
                    self.sock.sendto(data.encode(), (peer, MY_PORT))
                    print(f"[{self.lc}] → Enviado a {peer}: {message}")
                except:
                    pass

    def receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                received_lc, msg, sender_ip = data.decode().split(':', 2)
                received_lc = int(received_lc)

                # Actualizar reloj lógico según Lamport
                self.lc = max(self.lc, received_lc) + 1

                print(f"[{self.lc}] ← Recibido de {sender_ip}: {msg}")
            except Exception as e:
                print(f"Error recibiendo: {e}")

if __name__ == "__main__":
    node = LamportUDP()
    
    # Hilo para recibir mensajes
    threading.Thread(target=node.receive, daemon=True).start()
    
    print("Escribe mensajes (escribe 'exit' para salir):")
    while True:
        msg = input()
        if msg.lower() == 'exit':
            break
        node.send_message(msg)