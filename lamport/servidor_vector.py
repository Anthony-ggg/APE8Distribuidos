#!/usr/bin/env python3
"""
=============================================================
VECTORES DE TIEMPO (Vector Clocks) - SERVIDOR (Proceso 0)
=============================================================
Implementa relojes vectoriales para 5 procesos.
Permite detectar eventos concurrentes y establecer
causalidad en un sistema distribuido.

VECTOR DE TIEMPO: V = [V[0], V[1], V[2], V[3], V[4]]
  Cada posición corresponde a un proceso (0..4)
  Este servidor es el PROCESO 0.

REGLAS:
  1. Evento LOCAL:      V[i] += 1
  2. Al ENVIAR msg:     V[i] += 1  → adjuntar V completo
  3. Al RECIBIR msg M:  V[j] = max(V[j], M.V[j]) para todo j
                        luego V[i] += 1

DETECCIÓN DE CONCURRENCIA:
  A → B  (A causa B):     A.V[i] ≤ B.V[i] para todo i, con al menos un A.V[k] < B.V[k]
  A || B (concurrentes):  ¬(A→B) y ¬(B→A)

EJECUTAR:
    python3 servidor_vector.py

WIRESHARK: Filtrar con:  tcp.port == 8000
=============================================================
"""

import socket       # Sockets TCP
import threading    # Múltiples clientes
import time         # Timestamps reales
import json         # Para serializar el vector de tiempo

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
HOST        = '0.0.0.0'
PORT        = 8000
NUM_PROCESOS = 5       # Tamaño del vector
MI_ID       = 0       # Este servidor es el proceso 0

# ─────────────────────────────────────────────
#  VECTOR DE TIEMPO (compartido entre hilos)
# ─────────────────────────────────────────────
vector = [0] * NUM_PROCESOS   # V = [0, 0, 0, 0, 0]
lock_vector = threading.Lock()  # Protección de concurrencia

def vector_str(v=None):
    """Retorna el vector como string legible, ej: [1, 0, 3, 0, 2]"""
    v = v if v is not None else vector
    return str(v)

def tick_local():
    """
    Regla 1 y 2: Evento local o preparación de envío.
    Incrementa V[MI_ID] y retorna una copia del vector.
    """
    with lock_vector:
        vector[MI_ID] += 1
        return list(vector)   # Retornar copia para no compartir referencia

def tick_recepcion(v_recibido):
    """
    Regla 3: Al recibir un mensaje con vector V_recv.
    Para cada j: V[j] = max(V[j], V_recv[j])
    Luego: V[MI_ID] += 1
    Retorna (vector_antes, vector_despues).
    """
    with lock_vector:
        v_antes = list(vector)

        # max elemento a elemento
        for j in range(NUM_PROCESOS):
            vector[j] = max(vector[j], v_recibido[j])

        # Incrementar nuestra posición (evento de recepción)
        vector[MI_ID] += 1

        v_despues = list(vector)
        return v_antes, v_despues

def comparar_vectores(va, vb):
    """
    Compara dos vectores de tiempo y determina la relación causal.
    Retorna:
      'A → B'   si va ocurrió antes que vb (va causa vb)
      'B → A'   si vb ocurrió antes que va
      'A || B'  si son concurrentes (ninguno causó al otro)
      'A = B'   si son idénticos
    """
    a_menor_o_igual = all(va[i] <= vb[i] for i in range(NUM_PROCESOS))
    b_menor_o_igual = all(vb[i] <= va[i] for i in range(NUM_PROCESOS))

    if va == vb:
        return "A = B  (idénticos)"
    elif a_menor_o_igual:
        return "A → B  (A causalmente ANTES de B)"
    elif b_menor_o_igual:
        return "B → A  (B causalmente ANTES de A)"
    else:
        return "A || B (CONCURRENTES — no hay relación causal)"

def log_vector(evento, v_antes, v_despues, extra=""):
    """Imprime el estado del vector de forma visual."""
    print(f"\n  ┌─ {evento} {'─'*(44-len(evento))}")
    if extra:
        print(f"  │  {extra}")
    print(f"  │  Vector ANTES:  {vector_str(v_antes)}")
    print(f"  │  Vector DESPUÉS:{vector_str(v_despues)}")
    print(f"  └{'─'*50}", flush=True)

def manejar_cliente(conn, addr):
    """Maneja mensajes de un cliente: actualiza vector y responde."""

    ultimo_vector_cliente = None   # Para detectar concurrencia
    buffer = ""

    print(f"\n[CONEXIÓN] Cliente {addr} conectado.")

    try:
        while True:
            fragmento = conn.recv(2048).decode('utf-8')
            if not fragmento:
                break
            buffer += fragmento

            while '\n' in buffer:
                linea, buffer = buffer.split('\n', 1)
                linea = linea.strip()
                if not linea:
                    continue

                # Parsear: {"tipo": "MSG", "proceso": N, "vector": [...], "contenido": "..."}
                try:
                    datos = json.loads(linea)
                except json.JSONDecodeError:
                    print(f"  [ERROR JSON] '{linea[:60]}'")
                    continue

                if datos.get('tipo') == 'MSG':
                    id_remoto    = datos['proceso']
                    v_recibido   = datos['vector']
                    contenido    = datos['contenido']

                    print(f"\n  [RECIBIDO] Proceso {id_remoto} | V_remoto={v_recibido}")
                    print(f"  Contenido: '{contenido}'")

                    # ── Actualizar vector al recibir ───────────────
                    v_antes, v_despues = tick_recepcion(v_recibido)

                    log_vector(
                        evento=f"RECEPCIÓN desde Proceso {id_remoto}",
                        v_antes=v_antes,
                        v_despues=v_despues,
                        extra=f"V_remoto recibido: {v_recibido}"
                    )

                    # ── Detectar concurrencia con el evento anterior ─
                    if ultimo_vector_cliente is not None:
                        relacion = comparar_vectores(ultimo_vector_cliente, v_recibido)
                        print(f"  [CAUSALIDAD] V_anterior vs V_actual: {relacion}")

                    ultimo_vector_cliente = list(v_recibido)

                    # ── Preparar y enviar ACK ──────────────────────
                    v_antes_env = list(vector)
                    v_ack = tick_local()   # Evento de envío

                    log_vector(
                        evento="ENVÍO (ACK)",
                        v_antes=v_antes_env,
                        v_despues=v_ack,
                        extra=f"Respondiendo a Proceso {id_remoto}"
                    )

                    respuesta = json.dumps({
                        "tipo":    "ACK",
                        "proceso": MI_ID,
                        "vector":  v_ack
                    }) + "\n"

                    conn.sendall(respuesta.encode('utf-8'))

    except (ConnectionResetError, BrokenPipeError):
        print(f"\n[INFO] Cliente {addr} desconectado.")
    except Exception as e:
        print(f"\n[ERROR] {addr}: {e}")
    finally:
        conn.close()

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(10)

    print("=" * 60)
    print(f"  VECTORES DE TIEMPO — Proceso {MI_ID} (Servidor)")
    print("=" * 60)
    print(f"  Puerto: {PORT} (TCP) | Procesos totales: {NUM_PROCESOS}")
    print(f"  Vector inicial: {vector_str()}")
    print("  Esperando clientes... (Ctrl+C para detener)")
    print("=" * 60)

    # Evento local de inicio
    v_inicio = tick_local()
    log_vector("LOCAL (inicio del servidor)", [0]*NUM_PROCESOS, v_inicio)

    try:
        while True:
            conn, addr = srv.accept()
            hilo = threading.Thread(
                target=manejar_cliente, args=(conn, addr), daemon=True
            )
            hilo.start()
    except KeyboardInterrupt:
        print("\n\n[INFO] Servidor Vector Clock detenido.")
    finally:
        srv.close()

if __name__ == "__main__":
    main()
