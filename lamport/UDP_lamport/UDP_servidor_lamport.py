import socket
import os

MI_IP = "192.168.1.13"  # <-- Cambia por tu IP de la Fase 1
PUERTO = 5000
ARCHIVO_RELOJ = "reloj_local.txt"

def leer_reloj():
    if not os.path.exists(ARCHIVO_RELOJ):
        return 0
    with open(ARCHIVO_RELOJ, "r") as f:
        return int(f.read().strip())

def guardar_reloj(valor):
    with open(ARCHIVO_RELOJ, "w") as f:
        f.write(str(valor))

# Inicializar socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((MI_IP, PUERTO))

print(f"=== SERVIDOR UDP LAMPORT ESCUCHANDO EN {MI_IP}:{PUERTO} ===")

while True:
    data, addr = sock.recvfrom(1024)
    payload = data.decode('utf-8')
    
    # Decodificar el payload "reloj|mensaje"
    reloj_recibido_str, texto = payload.split('|', 1)
    reloj_recibido = int(reloj_recibido_str)
    
    reloj_actual = leer_reloj()
    
    # REGLA DE LAMPORT AL RECIBIR: max(Mi_Contador, Contador_Recibido) + 1
    nuevo_reloj = max(reloj_actual, reloj_recibido) + 1
    guardar_reloj(nuevo_reloj)
    
    print(f"\n[📩 UDP Recibido desde {addr[0]}]")
    print(f"   Mensaje : \"{texto}\"")
    print(f"   Reloj del Emisor : {reloj_recibido}")
    print(f"   Mi Reloj Anterior: {reloj_actual}")
    print(f"   👉 Mi Nuevo Reloj : {nuevo_reloj}")