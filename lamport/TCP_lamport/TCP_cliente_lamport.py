import socket
import os

ARCHIVO_RELOJ = "reloj_local.txt"

def leer_reloj():
    if not os.path.exists(ARCHIVO_RELOJ):
        return 0
    with open(ARCHIVO_RELOJ, "r") as f:
        return int(f.read().strip())

def guardar_reloj(valor):
    with open(ARCHIVO_RELOJ, "w") as f:
        f.write(str(valor))

print("=== CLIENTE TCP LAMPORT ===")
ip_destino = input("IP destino del compañero: ").strip()
texto_mensaje = input("Escribe el mensaje: ").strip()

# Regla de Lamport al enviar
reloj_actual = leer_reloj()
nuevo_reloj = reloj_actual + 1
guardar_reloj(nuevo_reloj)

payload = f"{nuevo_reloj}|{texto_mensaje}"

# Establecer flujo TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect((ip_destino, 6000))
    sock.send(payload.encode('utf-8'))
    print(f" [📤 TCP Enviado] Conexión exitosa.")
    print(f"   Payload: '{payload}' | 👉 Mi Reloj Actualizado: {nuevo_reloj}\n")
except Exception as e:
    print(f"❌ Error de conexión TCP: {e}")
    # Si falló el envío, revertimos el reloj para no generar saltos falsos
    guardar_reloj(reloj_actual)
finally:
    sock.close()