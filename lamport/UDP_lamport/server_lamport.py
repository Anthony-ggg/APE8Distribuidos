import socket
import threading

class LamportUDPServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.lc = 0
        self.clients = []  # Guardar direcciones de clientes

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        print(f"✅ Servidor UDP Lamport escuchando en {self.host}:{self.port}")

        while True:
            data, addr = sock.recvfrom(1024)
            if addr not in self.clients:
                self.clients.append(addr)
            
            received_lc, msg = map(int, data.decode().split(':', 1)) if ':' in data.decode() else (0, data.decode())
            
            # Regla de Lamport
            self.lc = max(self.lc, received_lc) + 1
            print(f"[{self.lc}] ← Recibido de {addr}: {msg}")

            # Reenviar a todos los clientes
            for client_addr in self.clients:
                if client_addr != addr:  # No reenviar al que lo envió
                    forward_msg = f"{self.lc}:{msg}"
                    sock.sendto(forward_msg.encode(), client_addr)
                    print(f"[{self.lc}] → Reenviado a {client_addr}")

if __name__ == "__main__":
    server = LamportUDPServer()
    server.start()