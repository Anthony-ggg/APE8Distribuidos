#!/usr/bin/env python3
"""
=============================================================
RELOJES LÓGICOS DE LAMPORT - CLIENTE (Proceso B)
=============================================================
El cliente envía mensajes al servidor con su timestamp de
Lamport adjunto. Al recibir la respuesta, actualiza su
propio reloj siguiendo las reglas de Lamport.

EJECUTAR:
    python3 cliente_lamport.py

    Para varias instancias simultáneas (probar concurrencia):
    python3 cliente_lamport.py &
    python3 cliente_lamport.py &
    python3 cliente_lamport.py

WIRESHARK: Filtrar con:  tcp.port == 7000
=============================================================
"""

import socket   # Sockets TCP
import time     # Para timestamps reales y pausas
import random   # Para intervalos aleatorios entre mensajes

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
SERVER_HOST   = '192.168.1.10'   # IP del servidor (cambia en LAN)
SERVER_PORT   = 7001
NOMBRE_PROCESO = "PROCESO_B (Cliente)"
NUM_MENSAJES  = 8             # Cuántos mensajes enviar

# ─────────────────────────────────────────────
#  RELOJ LÓGICO DE LAMPORT (local al cliente)
# ─────────────────────────────────────────────
reloj_lamport = 0

def tick_local():
    """Evento local: L = L + 1."""
    global reloj_lamport
    reloj_lamport += 1
    return reloj_lamport

def tick_envio():
    """Antes de enviar: L = L + 1."""
    return tick_local()

def tick_recepcion(timestamp_recibido):
    """Al recibir: L = max(L, ts_recibido) + 1."""
    global reloj_lamport
    reloj_lamport = max(reloj_lamport, timestamp_recibido) + 1
    return reloj_lamport

def log_evento(tipo, descripcion, reloj_antes=None, reloj_despues=None):
    """Imprime evento con formato para análisis de causalidad."""
    timestamp_real = time.strftime('%H:%M:%S')
    print(f"\n  {'─'*50}")
    print(f"  [{timestamp_real}] EVENTO: {tipo}")
    print(f"  Descripción: {descripcion}")
    if reloj_antes is not None:
        print(f"  Reloj ANTES:  L = {reloj_antes}")
    if reloj_despues is not None:
        print(f"  Reloj DESPUÉS: L = {reloj_despues}")
    print(f"  {'─'*50}", flush=True)

def main():
    print("=" * 60)
    print(f"  RELOJES LÓGICOS DE LAMPORT — {NOMBRE_PROCESO}")
    print("=" * 60)
    print(f"  Servidor: {SERVER_HOST}:{SERVER_PORT}")
    print(f"  Reloj inicial: L = {reloj_lamport}")
    print(f"  Mensajes a enviar: {NUM_MENSAJES}")
    print("=" * 60)

    # Crear socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[CONECTADO] Al servidor {SERVER_HOST}:{SERVER_PORT}")

        # ── Evento local: conexión establecida ─────────────────────
        reloj_antes = reloj_lamport
        reloj_conn = tick_local()
        log_evento(
            tipo="LOCAL (conexión)",
            descripcion=f"Conectado a {SERVER_HOST}:{SERVER_PORT}",
            reloj_antes=reloj_antes,
            reloj_despues=reloj_conn
        )

        buffer = ""   # Buffer de recepción

        for i in range(1, NUM_MENSAJES + 1):
            # ── Evento local antes de enviar ───────────────────────
            reloj_antes_local = reloj_lamport
            reloj_local = tick_local()
            log_evento(
                tipo="LOCAL (preparación)",
                descripcion=f"Preparando mensaje #{i}",
                reloj_antes=reloj_antes_local,
                reloj_despues=reloj_local
            )

            # ── REGLA 2: Incrementar reloj al enviar ───────────────
            reloj_antes_env = reloj_lamport
            ts_envio = tick_envio()

            contenido = f"Mensaje-{i}-de-{NOMBRE_PROCESO}"
            mensaje = f"MSG:{ts_envio}:{contenido}\n"

            sock.sendall(mensaje.encode('utf-8'))

            log_evento(
                tipo="ENVÍO",
                descripcion=f"Contenido: '{contenido}' | TS={ts_envio}",
                reloj_antes=reloj_antes_env,
                reloj_despues=ts_envio
            )

            # ── Recibir ACK del servidor ───────────────────────────
            while '\n' not in buffer:
                fragmento = sock.recv(1024).decode('utf-8')
                if not fragmento:
                    raise ConnectionError("Servidor desconectado")
                buffer += fragmento

            linea, buffer = buffer.split('\n', 1)
            linea = linea.strip()

            # Parsear respuesta: "ACK:<timestamp>:ok"
            partes = linea.split(':', 2)
            if len(partes) == 3 and partes[0] == "ACK":
                ts_ack = int(partes[1])

                reloj_antes_recv = reloj_lamport

                # REGLA 3: actualizar al recibir ACK
                reloj_nuevo = tick_recepcion(ts_ack)

                log_evento(
                    tipo="RECEPCIÓN (ACK)",
                    descripcion=f"ACK recibido | TS_servidor={ts_ack}",
                    reloj_antes=reloj_antes_recv,
                    reloj_despues=reloj_nuevo
                )

                # ── Verificar causalidad ───────────────────────────
                if reloj_nuevo > ts_ack:
                    print(f"  [CAUSALIDAD] Mi reloj ({reloj_nuevo}) > TS servidor ({ts_ack})")
                    print(f"               → Este proceso tiene eventos más recientes.")
                elif reloj_nuevo == ts_ack + 1:
                    print(f"  [CAUSALIDAD] Relojes sincronizados correctamente.")

            # Esperar un intervalo aleatorio entre mensajes (simula trabajo)
            pausa = random.uniform(0.5, 1.5)
            print(f"\n  [PAUSA] {pausa:.2f}s antes del próximo mensaje...")
            time.sleep(pausa)

    except ConnectionRefusedError:
        print(f"\n[ERROR] No se pudo conectar a {SERVER_HOST}:{SERVER_PORT}")
        print("[ERROR] ¿Está ejecutándose el servidor?")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        sock.close()
        print(f"\n[FIN] Reloj final del cliente: L = {reloj_lamport}")
        print("[FIN] Conexión cerrada.")

if __name__ == "__main__":
    main()
