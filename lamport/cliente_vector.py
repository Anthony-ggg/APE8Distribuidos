#!/usr/bin/env python3
"""
=============================================================
VECTORES DE TIEMPO (Vector Clocks) - CLIENTE
=============================================================
El cliente representa un proceso con su propio vector de
tiempo. Envía mensajes al servidor (Proceso 0) y actualiza
su vector en cada evento.

EJECUTAR (en terminales distintas, cambiando el ID):
    python3 cliente_vector.py --id 1
    python3 cliente_vector.py --id 2
    python3 cliente_vector.py --id 3
    python3 cliente_vector.py --id 4

Cada instancia es un proceso diferente en el sistema.

WIRESHARK: Filtrar con:  tcp.port == 8000
=============================================================
"""

import socket   # Sockets TCP
import time     # Para timestamps y pausas
import json     # Para serializar el vector de tiempo
import sys      # Para leer argumentos
import random   # Para intervalos aleatorios

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
SERVER_HOST  = '192.168.1.10'   # IP del servidor (cambia en LAN)
SERVER_PORT  = 7000
NUM_PROCESOS = 5

# Leer el ID de este proceso desde argumento de línea de comandos
if '--id' in sys.argv:
    idx = sys.argv.index('--id')
    MI_ID = int(sys.argv[idx + 1])
else:
    MI_ID = 1   # Por defecto es el proceso 1

NUM_MENSAJES = 6   # Cuántos mensajes enviar

# ─────────────────────────────────────────────
#  VECTOR DE TIEMPO LOCAL
# ─────────────────────────────────────────────
vector = [0] * NUM_PROCESOS   # Todas las posiciones en 0

def vector_str(v=None):
    v = v if v is not None else vector
    return str(v)

def tick_local():
    """Evento local: V[MI_ID] += 1."""
    vector[MI_ID] += 1
    return list(vector)

def tick_recepcion(v_recibido):
    """Al recibir: max elemento a elemento, luego V[MI_ID] += 1."""
    v_antes = list(vector)
    for j in range(NUM_PROCESOS):
        vector[j] = max(vector[j], v_recibido[j])
    vector[MI_ID] += 1
    return v_antes, list(vector)

def comparar_vectores(va, vb, nombre_a="A", nombre_b="B"):
    """Determina la relación causal entre dos vectores."""
    a_le_b = all(va[i] <= vb[i] for i in range(NUM_PROCESOS))
    b_le_a = all(vb[i] <= va[i] for i in range(NUM_PROCESOS))

    if va == vb:
        return f"{nombre_a} = {nombre_b}  (idénticos)"
    elif a_le_b:
        return f"{nombre_a} → {nombre_b}  ({nombre_a} causalmente ANTES)"
    elif b_le_a:
        return f"{nombre_b} → {nombre_a}  ({nombre_b} causalmente ANTES)"
    else:
        return f"{nombre_a} || {nombre_b}  (CONCURRENTES ← evento interesante!)"

def log_vector(evento, v_antes, v_despues, extra=""):
    """Imprime el estado del vector de tiempo."""
    print(f"\n  ┌─ {evento} {'─'*(44-len(evento))}")
    if extra:
        print(f"  │  {extra}")
    print(f"  │  Vector ANTES:  {vector_str(v_antes)}")
    print(f"  │  Vector DESPUÉS:{vector_str(v_despues)}")
    print(f"  └{'─'*50}", flush=True)

def main():
    print("=" * 60)
    print(f"  VECTORES DE TIEMPO — Proceso {MI_ID} (Cliente)")
    print("=" * 60)
    print(f"  Servidor: {SERVER_HOST}:{SERVER_PORT}")
    print(f"  MI_ID = {MI_ID} | Tamaño vector = {NUM_PROCESOS}")
    print(f"  Vector inicial: {vector_str()}")
    print("=" * 60)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    buffer = ""
    historial_vectores = []   # Para comparar eventos y detectar concurrencia

    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"\n[CONECTADO] Al servidor Proceso 0 en {SERVER_HOST}:{SERVER_PORT}")

        # ── Evento local al conectar ─────────────────────────────────
        v_antes_conn = list(vector)
        v_conn = tick_local()
        log_vector("LOCAL (conexión establecida)", v_antes_conn, v_conn)

        for i in range(1, NUM_MENSAJES + 1):
            # ── Evento local (trabajo del proceso) ──────────────────
            v_antes_local = list(vector)
            v_local = tick_local()
            log_vector(
                f"LOCAL (trabajo #{i})",
                v_antes_local, v_local,
                extra=f"Proceso {MI_ID} realiza trabajo interno"
            )

            # ── Incrementar vector al ENVIAR ────────────────────────
            v_antes_env = list(vector)
            v_envio = tick_local()   # V[MI_ID] += 1 antes de enviar

            contenido = f"Evento-{i} del Proceso-{MI_ID}"

            # Serializar el mensaje con el vector de tiempo completo
            mensaje = json.dumps({
                "tipo":     "MSG",
                "proceso":  MI_ID,
                "vector":   v_envio,   # Adjuntar vector completo
                "contenido": contenido
            }) + "\n"

            sock.sendall(mensaje.encode('utf-8'))

            log_vector(
                f"ENVÍO mensaje #{i}",
                v_antes_env, v_envio,
                extra=f"Contenido: '{contenido}'"
            )

            historial_vectores.append(list(v_envio))

            # ── Recibir ACK del servidor ─────────────────────────────
            while '\n' not in buffer:
                fragmento = sock.recv(2048).decode('utf-8')
                if not fragmento:
                    raise ConnectionError("Servidor desconectado")
                buffer += fragmento

            linea, buffer = buffer.split('\n', 1)
            linea = linea.strip()

            try:
                ack = json.loads(linea)
            except json.JSONDecodeError:
                print(f"  [ERROR JSON] '{linea[:60]}'")
                continue

            if ack.get('tipo') == 'ACK':
                v_ack_servidor = ack['vector']

                v_antes_recv = list(vector)
                v_recv, v_despues_recv = tick_recepcion(v_ack_servidor)

                log_vector(
                    f"RECEPCIÓN ACK #{i}",
                    v_antes_recv, v_despues_recv,
                    extra=f"V_servidor recibido: {v_ack_servidor}"
                )

                # ── Comparar con el vector que enviamos ─────────────
                relacion = comparar_vectores(
                    v_envio, v_ack_servidor,
                    nombre_a=f"P{MI_ID}(envío)", nombre_b="P0(ACK)"
                )
                print(f"  [CAUSALIDAD] {relacion}")

            # Pausa aleatoria para simular trabajo asincrónico
            pausa = random.uniform(0.3, 1.2)
            print(f"\n  [PAUSA] {pausa:.2f}s...")
            time.sleep(pausa)

        # ── Resumen final de causalidad ──────────────────────────────
        print("\n" + "=" * 60)
        print("  RESUMEN: ANÁLISIS DE CAUSALIDAD ENTRE EVENTOS PROPIOS")
        print("=" * 60)
        for idx_a in range(len(historial_vectores)):
            for idx_b in range(idx_a + 1, len(historial_vectores)):
                va = historial_vectores[idx_a]
                vb = historial_vectores[idx_b]
                relacion = comparar_vectores(va, vb, f"E{idx_a+1}", f"E{idx_b+1}")
                print(f"  E{idx_a+1}={va} vs E{idx_b+1}={vb}")
                print(f"  → {relacion}\n")

    except ConnectionRefusedError:
        print(f"\n[ERROR] No se pudo conectar. ¿El servidor está activo?")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        sock.close()
        print(f"\n[FIN] Vector final del Proceso {MI_ID}: {vector_str()}")
        print("[FIN] Conexión cerrada.")

if __name__ == "__main__":
    main()
