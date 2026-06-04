import socket
import threading

SERVER_IP = "192.168.1.10"
PORT = 5000

class LamportUDPClient:
    def __init__(self):
        self.lc = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))  # Puerto efímero
        print("✅ Cliente UDP Lamport iniciado")

    def send_message(self, message):
        self.lc += 1
        data = f"{self.lc}:{message}"
        self.sock.sendto(data.encode(), (SERVER_IP, PORT))
        print(f"[{self.lc}] → Enviado al servidor: {message}")

    def receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                received_lc, msg = map(int, data.decode().split(':', 1))
                self.lc = max(self.lc, received_lc) + 1
                print(f"[{self.lc}] ← Recibido: {msg}")
            except:
                pass

if __name__ == "__main__":
    client = LamportUDPClient()
    threading.Thread(target=client.receive, daemon=True).start()

    print("Escribe mensajes (exit para salir):")
    while True:
        msg = input()
        if msg.lower() == 'exit':
            break
        client.send_message(msg)