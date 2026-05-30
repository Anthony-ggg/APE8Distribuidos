#!/usr/bin/env python3
"""
=============================================================
ALGORITMO DE CRISTIAN - SERVIDOR (Servidor de Tiempo)
=============================================================
El servidor de Cristian responde a solicitudes de tiempo de
los clientes. Cada cliente puede calcular el RTT y ajustar
su reloj local con base en la respuesta del servidor.

EJECUTAR:
    python3 servidor_cristian.py

PROTOCOLO UDP:
    Cliente  --[REQUEST_TIME]--> Servidor
    Cliente <--[TIMESTAMP]------ Servidor

WIRESHARK: Filtrar con:  udp.port == 5000
=============================================================
"""

import socket       # Para crear sockets UDP
import time         # Para obtener timestamps reales
import struct       # Para empaquetar el tiempo en bytes

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — modifica estas variables
#  para adaptarlas a tu red LAN
# ─────────────────────────────────────────────
HOST = '0.0.0.0'   # Escucha en todas las interfaces de red
PORT = 5000         # Puerto UDP del servidor de tiempo

def iniciar_servidor():
    """Crea el socket UDP y atiende solicitudes de tiempo indefinidamente."""

    # Crear socket UDP (SOCK_DGRAM = sin conexión, sin handshake)
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # SO_REUSEADDR permite reusar el puerto si el proceso anterior terminó mal
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Asociar el socket a la dirección y puerto
    servidor.bind((HOST, PORT))

    print("=" * 60)
    print("  SERVIDOR DE TIEMPO - ALGORITMO DE CRISTIAN")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT} (UDP)")
    print(f"  Hora actual del servidor: {time.strftime('%H:%M:%S')}")
    print("  Esperando clientes... (Ctrl+C para detener)")
    print("=" * 60)

    try:
        while True:
            # Bloquear hasta recibir un datagrama de cualquier cliente
            # datos: bytes recibidos | direccion: (ip, puerto) del cliente
            datos, direccion = servidor.recvfrom(1024)

            # Registrar el instante EXACTO de recepción (T_server_recv)
            t_recepcion = time.time()

            mensaje = datos.decode('utf-8').strip()
            print(f"\n[RECIBIDO]  Cliente: {direccion} | Mensaje: '{mensaje}' | T_recv: {t_recepcion:.6f}")

            if mensaje == "REQUEST_TIME":
                # Obtener timestamp actual del servidor para enviarlo
                # Nota: tomamos el tiempo DESPUÉS de procesar para mayor precisión
                t_respuesta = time.time()

                # Empaquetar el timestamp como double de 8 bytes (big-endian)
                # Esto garantiza que el cliente lo interprete correctamente
                payload = struct.pack('!d', t_respuesta)

                # Enviar el timestamp de vuelta al cliente
                servidor.sendto(payload, direccion)

                print(f"[ENVIADO]   → {direccion} | T_respuesta: {t_respuesta:.6f}")
                print(f"            Hora legible: {time.strftime('%H:%M:%S', time.localtime(t_respuesta))}")

            else:
                # Mensaje desconocido: ignorar con un log
                print(f"[IGNORADO]  Mensaje desconocido de {direccion}: '{mensaje}'")

    except KeyboardInterrupt:
        print("\n\n[INFO] Servidor detenido por el usuario.")
    finally:
        servidor.close()   # Liberar el socket siempre
        print("[INFO] Socket cerrado correctamente.")

# Punto de entrada del script
if __name__ == "__main__":
    iniciar_servidor()
