#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - CLIENTE UDP
=============================================================
Implementa los relojes de vectores usando el protocolo UDP.

EJECUTAR:
    python3 cliente_vector_udp.py

WIRESHARK: Filtrar con:  udp.port == 8000
=============================================================
"""

import socket
import threading
import time
import json

HOST = '127.0.0.1'  # IP del servidor
PORT = 8000
MI_ID = "C"  # ID de este proceso (Cliente)

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

def recibir_mensajes(sock):
    """Hilo para escuchar respuestas del servidor (ACKs) por UDP."""
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            linea = data.decode('utf-8').strip()
            
            partes = linea.split(':', 1)
            if len(partes) == 2 and partes[0] == "ACK":
                vector_str = partes[1]
                try:
                    vector_remoto = json.loads(vector_str)
                except json.JSONDecodeError:
                    print("Error decodificando vector JSON.")
                    continue

                vector_antes = dict(reloj_vector)
                vector_nuevo = tick_recepcion(vector_remoto)

                log_evento(
                    tipo="RECEPCIÓN",
                    descripcion=f"ACK recibido de {addr} | Vector Recibido={vector_remoto}",
                    vector_antes=vector_antes,
                    vector_despues=vector_nuevo
                )
    except Exception as e:
        # El socket se cierra al salir
        pass

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("=" * 60)
    print("  RELOJES DE VECTORES — CLIENTE UDP (Proceso C)")
    print("=" * 60)
    print(f"  Servidor objetivo: {HOST}:{PORT}")
    print(f"  Vector inicial: {reloj_vector}")
    print("=" * 60)

    # Iniciar hilo para recibir respuestas
    hilo_recepcion = threading.Thread(target=recibir_mensajes, args=(sock,), daemon=True)
    hilo_recepcion.start()

    print("\n[INSTRUCCIONES]")
    print(" - Escribe 'enviar' para mandar un paquete UDP al servidor")
    print(" - Escribe 'local' para simular un evento interno en el cliente")
    print(" - Escribe 'salir' para cerrar\n")

    try:
        while True:
            comando = input("Comando > ").strip().lower()
            if comando == 'salir':
                break
            elif comando == 'local':
                v_antes = dict(reloj_vector)
                v_despues = tick_local()
                log_evento(
                    tipo="LOCAL",
                    descripcion="Evento interno del cliente",
                    vector_antes=v_antes,
                    vector_despues=v_despues
                )
            elif comando == 'enviar':
                v_antes = dict(reloj_vector)
                v_envio = tick_envio()
                mensaje = f"MSG:{json.dumps(v_envio)}:Hola_desde_cliente"
                
                # Enviar directo por UDP sin conectar
                sock.sendto(mensaje.encode('utf-8'), (HOST, PORT))
                
                log_evento(
                    tipo="ENVÍO",
                    descripcion="Enviando datagrama UDP al servidor",
                    vector_antes=v_antes,
                    vector_despues=v_envio
                )
            elif comando != "":
                print("Comando no reconocido. Usa: enviar, local, salir.")
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print("\n[DESCONEXIÓN] Cliente UDP cerrado.")

if __name__ == "__main__":
    main()
