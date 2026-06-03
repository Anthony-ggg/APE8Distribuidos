#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - SERVIDOR (Proceso S)
=============================================================
Implementa los relojes de vectores para mantener la
causalidad exacta en un sistema distribuido.

REGLAS DE VECTORES:
  1. Evento LOCAL en Proceso i:  V[i] = V[i] + 1
  2. Al ENVIAR desde Proceso i:  V[i] = V[i] + 1 → adjuntar V
  3. Al RECIBIR msg con vector W en Proceso j:
        V[j] = V[j] + 1
        Para todo k: V[k] = max(V[k], W[k])

EJECUTAR:
    python3 servidor_vector.py

PROTOCOLO TCP:
  Nodo → Servidor: "MSG:<json_vector>:<contenido>"
  Servidor → Nodo:  "ACK:<json_vector>"

WIRESHARK: Filtrar con:  tcp.port == 8000
=============================================================
"""

import socket
import threading
import time
import json

HOST = '192.168.1.10'
PORT = 8008
MI_ID = "S"  # ID de este proceso (Servidor)

# Vector de tiempo inicial.enviar
# En un sistema real se descubre dinámicamente, aquí lo definimos.
reloj_vector = {"S": 0, "C": 0}
lock_reloj = threading.Lock()

def tick_local():
    """Regla 1: Incrementar el reloj propio (S)."""
    global reloj_vector
    with lock_reloj:
        reloj_vector[MI_ID] += 1
        return dict(reloj_vector)

def tick_envio():
    """Regla 2: Incrementar reloj propio antes de enviar."""
    return tick_local()

def tick_recepcion(vector_recibido):
    """
    Regla 3: Al recibir mensaje.
    Incrementar propio, y tomar el máximo de cada componente.
    """
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

def manejar_cliente(conn, addr):
    print(f"\n[CONEXIÓN] Cliente conectado: {addr}")
    buffer = ""

    try:
        while True:
            fragmento = conn.recv(1024).decode('utf-8')
            if not fragmento:
                break

            buffer += fragmento
            while '\n' in buffer:
                linea, buffer = buffer.split('\n', 1)
                linea = linea.strip()
                if not linea:
                    continue

                # Parsear: MSG|{"C": 1, "S": 0}|Hola
                partes = linea.split('|', 2)
                if len(partes) == 3 and partes[0] == "MSG":
                    vector_str = partes[1]
                    contenido = partes[2]
                    
                    try:
                        vector_remoto = json.loads(vector_str)
                    except json.JSONDecodeError:
                        print("Error decodificando vector JSON.")
                        continue

                    vector_antes = dict(reloj_vector)
                    
                    # REGLA 3
                    vector_nuevo = tick_recepcion(vector_remoto)

                    log_evento(
                        tipo="RECEPCIÓN",
                        descripcion=f"De {addr} | '{contenido}' | Vector Recibido={vector_remoto}",
                        vector_antes=vector_antes,
                        vector_despues=vector_nuevo
                    )

                    # Simular procesamiento
                    time.sleep(1)
                    
                    # REGLA 2: ENVÍO
                    vector_antes_env = dict(reloj_vector)
                    vector_ack = tick_envio()
                    
                    respuesta = f"ACK|{json.dumps(vector_ack)}\n"
                    conn.sendall(respuesta.encode('utf-8'))

                    log_evento(
                        tipo="ENVÍO (ACK)",
                        descripcion=f"Enviando ACK a {addr}",
                        vector_antes=vector_antes_env,
                        vector_despues=vector_ack
                    )
                else:
                    print(f"  [IGNORADO] Formato inválido: '{linea}'")

    except Exception as e:
        print(f"\n[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"\n[DESCONEXIÓN] Cliente {addr} cerrado.")

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)

    print("=" * 60)
    print("  RELOJES DE VECTORES — SERVIDOR (Proceso S)")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT}")
    print(f"  Vector inicial: {reloj_vector}")
    print("=" * 60)

    try:
        while True:
            conn, addr = servidor.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
            hilo.start()
    except KeyboardInterrupt:
        print("\n\n[INFO] Servidor detenido.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()
