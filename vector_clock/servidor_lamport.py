#!/usr/bin/env python3
"""
=============================================================
RELOJES LÓGICOS DE LAMPORT - SERVIDOR (Proceso A)
=============================================================
Implementa los relojes lógicos de Lamport para ordenar
eventos en un sistema distribuido sin reloj global.

REGLAS DE LAMPORT:
  1. Evento LOCAL:      L = L + 1
  2. Al ENVIAR:         L = L + 1  → adjuntar L al mensaje
  3. Al RECIBIR msg M:  L = max(L, M.timestamp) + 1

EJECUTAR:
    python3 servidor_lamport.py

PROTOCOLO TCP:
  Nodo → Servidor: "MSG:<timestamp>:<contenido>"
  Servidor → Nodo:  "ACK:<timestamp_servidor>"

WIRESHARK: Filtrar con:  tcp.port == 7000
=============================================================
"""

import socket       # Sockets TCP
import threading    # Para manejar múltiples clientes
import time         # Para timestamps reales
import sys          # Para flush de stdout

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
HOST = '0.0.0.0'
PORT = 7000
NOMBRE_PROCESO = "PROCESO_A (Servidor)"

# ─────────────────────────────────────────────
#  RELOJ LÓGICO DE LAMPORT (compartido)
# ─────────────────────────────────────────────
reloj_lamport = 0
lock_reloj = threading.Lock()   # Proteger acceso concurrente al reloj

def tick_local():
    """
    Regla 1: Evento local.
    Incrementa el reloj en 1 y retorna el nuevo valor.
    """
    global reloj_lamport
    with lock_reloj:
        reloj_lamport += 1
        return reloj_lamport

def tick_envio():
    """
    Regla 2: Antes de enviar un mensaje.
    Incrementa el reloj en 1 y retorna el timestamp a adjuntar.
    """
    return tick_local()   # Enviar = también un evento local

def tick_recepcion(timestamp_recibido):
    """
    Regla 3: Al recibir un mensaje con timestamp externo.
    L = max(L_local, timestamp_recibido) + 1

    Args:
        timestamp_recibido: el timestamp que llegó en el mensaje
    """
    global reloj_lamport
    with lock_reloj:
        reloj_lamport = max(reloj_lamport, timestamp_recibido) + 1
        return reloj_lamport

def log_evento(tipo, descripcion, reloj_antes=None, reloj_despues=None):
    """Imprime un evento con formato claro para análisis de causalidad."""
    timestamp_real = time.strftime('%H:%M:%S')
    print(f"\n  {'─'*50}")
    print(f"  [{timestamp_real}] EVENTO: {tipo}")
    print(f"  Descripción: {descripcion}")
    if reloj_antes is not None:
        print(f"  Reloj ANTES:  L = {reloj_antes}")
    if reloj_despues is not None:
        print(f"  Reloj DESPUÉS: L = {reloj_despues}")
    print(f"  {'─'*50}", flush=True)

def manejar_cliente(conn, addr):
    """
    Maneja la comunicación con un cliente:
    recibe mensajes, actualiza el reloj y responde con ACK.
    """
    print(f"\n[CONEXIÓN] Cliente conectado: {addr}")
    buffer = ""   # Acumular datos hasta recibir una línea completa

    try:
        while True:
            # Recibir datos en fragmentos
            fragmento = conn.recv(1024).decode('utf-8')
            if not fragmento:
                break   # El cliente cerró la conexión

            buffer += fragmento

            # Procesar líneas completas (separadas por '\n')
            while '\n' in buffer:
                linea, buffer = buffer.split('\n', 1)
                linea = linea.strip()
                if not linea:
                    continue

                # ── Parsear mensaje: "MSG:<timestamp>:<contenido>" ──
                partes = linea.split(':', 2)
                if len(partes) == 3 and partes[0] == "MSG":
                    ts_remoto  = int(partes[1])
                    contenido  = partes[2]

                    reloj_antes = reloj_lamport

                    # REGLA 3: actualizar reloj al recibir
                    reloj_nuevo = tick_recepcion(ts_remoto)

                    log_evento(
                        tipo="RECEPCIÓN",
                        descripcion=f"De {addr} | Contenido: '{contenido}' | "
                                    f"TS_remoto={ts_remoto}",
                        reloj_antes=reloj_antes,
                        reloj_despues=reloj_nuevo
                    )

                    # ── Registrar evento local de procesamiento ──────
                    reloj_antes_proc = reloj_lamport
                    reloj_proc = tick_local()
                    log_evento(
                        tipo="LOCAL (procesamiento)",
                        descripcion=f"Procesando mensaje de {addr}",
                        reloj_antes=reloj_antes_proc,
                        reloj_despues=reloj_proc
                    )

                    # ── REGLA 2: Actualizar reloj al ENVIAR ACK ──────
                    reloj_antes_env = reloj_lamport
                    ts_ack = tick_envio()

                    respuesta = f"ACK:{ts_ack}:ok\n"
                    conn.sendall(respuesta.encode('utf-8'))

                    log_evento(
                        tipo="ENVÍO (ACK)",
                        descripcion=f"Enviando ACK a {addr} con TS={ts_ack}",
                        reloj_antes=reloj_antes_env,
                        reloj_despues=ts_ack
                    )
                else:
                    print(f"  [IGNORADO] Formato inválido: '{linea}'")

    except ConnectionResetError:
        print(f"\n[INFO] Cliente {addr} desconectado abruptamente.")
    except Exception as e:
        print(f"\n[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"\n[DESCONEXIÓN] Cliente {addr} cerrado.")

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(10)   # Hasta 10 conexiones en cola

    print("=" * 60)
    print(f"  RELOJES LÓGICOS DE LAMPORT — {NOMBRE_PROCESO}")
    print("=" * 60)
    print(f"  Escuchando en {HOST}:{PORT} (TCP)")
    print(f"  Reloj inicial: L = {reloj_lamport}")
    print("  Esperando clientes... (Ctrl+C para detener)")
    print("=" * 60)

    # Evento de inicio del servidor (evento local)
    reloj_inicio = tick_local()
    log_evento(
        tipo="LOCAL (inicio)",
        descripcion="Servidor iniciado",
        reloj_antes=0,
        reloj_despues=reloj_inicio
    )

    try:
        while True:
            conn, addr = servidor.accept()
            # Crear un hilo para cada cliente
            hilo = threading.Thread(
                target=manejar_cliente,
                args=(conn, addr),
                daemon=True   # El hilo termina cuando el proceso principal termina
            )
            hilo.start()

    except KeyboardInterrupt:
        print("\n\n[INFO] Servidor Lamport detenido.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()
