import socket
import os

MI_IP = "192.168.1.13"  # <-- Cambia por tu IP de la Fase 1
PUERTO = 6000
ARCHIVO_RELOJ = "reloj_local.txt"

def leer_reloj():
    if not os.path.exists(ARCHIVO_RELOJ):
        return 0
    with open(ARCHIVO_RELOJ, "r") as f:
        return int(f.read().strip())

def guardar_reloj(valor):
    with open(ARCHIVO_RELOJ, "w") as f:
        f.write(str(valor))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((MI_IP, PUERTO))
server.listen(5)

print(f"=== SERVIDOR TCP LAMPORT ESCUCHANDO EN {MI_IP}:{PUERTO} ===")

while True:
    conn, addr = server.accept()
    data = conn.recv(1024).decode('utf-8')
    
    if data:
        reloj_recibido_str, texto = data.split('|', 1)
        reloj_recibido = int(reloj_recibido_str)
        
        reloj_actual = leer_reloj()
        
        # Regla de Lamport al recibir
        nuevo_reloj = max(reloj_actual, reloj_recibido) + 1
        guardar_reloj(nuevo_reloj)
        
        print(f"\n[📩 TCP Conexión desde {addr[0]}]")
        print(f"   Mensaje : \"{texto}\"")
        print(f"   Reloj del Emisor : {reloj_recibido}")
        print(f"   Mi Reloj Anterior: {reloj_actual}")
        print(f"   👉 Mi Nuevo Reloj : {nuevo_reloj}")
        
    conn.close()