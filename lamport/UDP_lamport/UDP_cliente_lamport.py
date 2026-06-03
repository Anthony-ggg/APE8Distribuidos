import socket
import os
import sys

ARCHIVO_RELOJ = "reloj_local.txt"

def leer_reloj():
    if not os.path.exists(ARCHIVO_RELOJ):
        return 0
    with open(ARCHIVO_RELOJ, "r") as f:
        return int(f.read().strip())

def guardar_reloj(valor):
    with open(ARCHIVO_RELOJ, "w") as f:
        f.write(str(valor))

print("=== CLIENTE UDP LAMPORT ===")
ip_destino = input("IP destino del compañero: ").strip()
texto_mensaje = input("Escribe el mensaje: ").strip()

# REGLA DE LAMPORT AL ENVIAR: Incrementar mi contador en 1
reloj_actual = leer_reloj()
nuevo_reloj = reloj_actual + 1
guardar_reloj(nuevo_reloj)

# Construir Payload
payload = f"{nuevo_reloj}|{texto_mensaje}"

# Enviar Datagrama
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(payload.encode('utf-8'), (ip_destino, 5000))
sock.close()

print(f" [📤 UDP Enviado] Payload: '{payload}' | 👉 Mi Reloj Actualizado: {nuevo_reloj}\n")