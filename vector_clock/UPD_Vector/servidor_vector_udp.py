#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - SERVIDOR UDP
=============================================================
Implementa los relojes de vectores usando el protocolo UDP.

EJECUTAR:
    python3 servidor_vector_udp.py

WIRESHARK: Filtrar con:  udp.port == 8000
=============================================================
"""

import socket
import threading
import time
import json

HOST = '192.168.1.10'
PORT = 8007
MI_ID = "S"  # ID de este proceso (Servidor)

reloj_vector = {"S": 0, "C": 0}
lock_reloj = threading.Lock()

def tick_local():
    global reloj_vector
    with lock_reloj:
        reloj_vector[MI_ID] += 1
        return dict(reloj_vector)

def tick_envio():
    return tick_local()

def tick_recepcion(vector_recibido):
    global reloj_vector
    with lock_reloj:
        reloj_vector[MI_ID] += 1
        for proc, val in vector_recibido.items():
            if proc in reloj_vector:
                reloj_vector[proc] = max(reloj_vector[proc], val)
            else:
                reloj_vector[proc] = val
        return dict(reloj_vector)

def log_evento(tipo, descripcion, vector_antes=None, vector_despues=None):
    timestamp_real = time.strftime('%H:%M:%S')
    print(f"\n  {'─'*60}")
    print(f"  [{timestamp_real}] EVENTO: {tipo}")
    print(f"  Descripción: {descripcion}")
    if vector_antes is not None:
        print(f"  Vector ANTES:  {vector_antes}")
    if vector_despues is not None:
        print(f"  Vector DESPUÉS: {vector_despues}")
    print(f"  {'─'*60}", flush=True)

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))

    print("=" * 60)
    print("  RELOJES DE VECTORES — SERVIDOR UDP (Proceso S)")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT} (UDP)")
    print(f"  Vector inicial: {reloj_vector}")
    print("=" * 60)

    try:
        while True:
            data, addr = servidor.recvfrom(1024)
            linea = data.decode('utf-8').strip()

            partes = linea.split(':', 2)
            if len(partes) == 3 and partes[0] == "MSG":
                vector_str = partes[1]
                contenido = partes[2]
                
                try:
                    vector_remoto = json.loads(vector_str)
                except json.JSONDecodeError:
                    print(f"[ERROR] JSON inválido desde {addr}")
                    continue

                vector_antes = dict(reloj_vector)
                
                # REGLA 3: RECEPCIÓN
                vector_nuevo = tick_recepcion(vector_remoto)

                log_evento(
                    tipo="RECEPCIÓN",
                    descripcion=f"De {addr} | '{contenido}' | Vector Recibido={vector_remoto}",
                    vector_antes=vector_antes,
                    vector_despues=vector_nuevo
                )

                # Simular procesamiento
                time.sleep(0.5)
                
                # REGLA 2: ENVÍO
                vector_antes_env = dict(reloj_vector)
                vector_ack = tick_envio()
                
                respuesta = f"ACK:{json.dumps(vector_ack)}"
                servidor.sendto(respuesta.encode('utf-8'), addr)

                log_evento(
                    tipo="ENVÍO (ACK)",
                    descripcion=f"Enviando ACK a {addr}",
                    vector_antes=vector_antes_env,
                    vector_despues=vector_ack
                )
            else:
                print(f"  [IGNORADO] Formato inválido desde {addr}: '{linea}'")

    except KeyboardInterrupt:
        print("\n\n[INFO] Servidor detenido.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()
