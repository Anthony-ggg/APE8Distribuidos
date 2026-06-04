import socket
import threading

class LamportServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.lc = 0  # Reloj lógico
        self.clients = []

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Servidor Lamport escuchando en {self.host}:{self.port} | LC inicial: 0")

        while True:
            client, addr = server.accept()
            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client, addr)).start()

    def handle_client(self, client, addr):
        print(f"Cliente conectado: {addr}")
        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break
                
                received_lc, msg = map(int, data.split(':', 1)) if ':' in data else (0, data)
                
                # Actualizar reloj lógico
                self.lc = max(self.lc, received_lc) + 1
                print(f"[{self.lc}] Recibido de {addr}: {msg} | LC actualizado")

                # Reenviar a otros clientes
                for c in self.clients:
                    if c != client:
                        c.send(f"{self.lc}:{msg}".encode())
            except:
                break
        client.close()

if __name__ == "__main__":
    server = LamportServer()
    server.start()