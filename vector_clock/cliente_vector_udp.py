#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - P2P UDP (5 POSICIONES)
=============================================================

CORRECCIONES APLICADAS:
  1. Validación estricta del argumento --id al iniciar (evita que todos
     arranquen como PC2 por defecto y pisen el mismo puerto).
  2. Un nodo NO puede enviarse un mensaje a sí mismo.
  3. El socket de escucha UDP se vincula a '0.0.0.0' para aceptar
     paquetes de cualquier interfaz (no solo loopback).
  4. Manejo de errores más robusto en el hilo receptor (no muere ante
     un paquete malformado; sigue escuchando).
  5. Confirmación visual del ID y puerto al arrancar.
"""

import socket
import threading
import json
import sys

# ── Vector estricto de 5 posiciones [PC1, PC2, PC3, PC4, PC5] ──────────────
MAPA_PROCESOS = {
    "PC1": 0,
    "PC2": 1,
    "PC3": 2,
    "PC4": 3,
    "PC5": 4,
}
reloj_vector = [0, 0, 0, 0, 0]

# ── Tabla de red ─────────────────────────────────────────────────────────────
# Descomentar PC4/PC5 si se usan físicamente.
TABLA_RED = {
    "PC1": ("192.168.1.10", 8001),
    "PC2": ("192.168.1.11", 8002),
    "PC3": ("192.168.1.12", 8003),
    # "PC4": ("192.168.1.13", 8004),
    # "PC5": ("192.168.1.14", 8005),
}

# ── FIX 1: El --id es OBLIGATORIO; sin él el programa no arranca ─────────────
if '--id' not in sys.argv:
    print("[ERROR] Debes indicar tu identidad con: python script.py --id PC1")
    print("        Valores válidos:", list(TABLA_RED.keys()))
    sys.exit(1)

MI_ID = sys.argv[sys.argv.index('--id') + 1].upper()

if MI_ID not in TABLA_RED:
    print(f"[ERROR] El ID '{MI_ID}' no existe o está comentado en TABLA_RED.")
    print("        Valores válidos:", list(TABLA_RED.keys()))
    sys.exit(1)

MI_INDICE = MAPA_PROCESOS[MI_ID]
MI_IP, MI_PUERTO = TABLA_RED[MI_ID]
lock_reloj = threading.Lock()


# ── Operaciones del reloj ─────────────────────────────────────────────────────
def tick_local():
    global reloj_vector
    with lock_reloj:
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)


def tick_envio():
    return tick_local()


def tick_recepcion(vector_recibido):
    global reloj_vector
    with lock_reloj:
        for i in range(5):
            reloj_vector[i] = max(reloj_vector[i], vector_recibido[i])
        reloj_vector[MI_INDICE] += 1
        return list(reloj_vector)


# ── Log ───────────────────────────────────────────────────────────────────────
def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*60}")
    print(f"  EVENTO: {tipo} en {MI_ID}")
    print(f"  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}")
    print(f"  Vector DESPUÉS: {v_despues}")
    print(f"  {'─'*60}", flush=True)


# ── Receptor UDP ──────────────────────────────────────────────────────────────
def escuchar_udp(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            paquete = json.loads(data.decode('utf-8'))
            v_antes = list(reloj_vector)
            v_nuevo = tick_recepcion(paquete["vector"])
            log_evento(
                "RECEPCIÓN",
                f"Desde {paquete['origen']} ({addr[0]}): '{paquete['mensaje']}'",
                v_antes,
                v_nuevo,
            )
        except json.JSONDecodeError:
            print("[WARN] Paquete malformado recibido, ignorado.")
        except OSError:
            # Socket cerrado al salir: terminar hilo limpiamente
            break
        except Exception as e:
            print(f"[WARN] Error en recepción UDP: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # FIX 3: bind en '0.0.0.0' para escuchar en todas las interfaces
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', MI_PUERTO))

    print("=" * 60)
    print(f"  RELOJES DE VECTORES UDP — NODO {MI_ID}")
    print("=" * 60)
    print(f"  Mi IP configurada : {MI_IP}  |  Puerto: {MI_PUERTO}")
    print(f"  Mi índice en vector: {MI_INDICE}")
    print(f"  Vector inicial     : {reloj_vector}")
    print(f"  Nodos activos      : {list(TABLA_RED.keys())}")
    print("=" * 60)

    threading.Thread(target=escuchar_udp, args=(sock,), daemon=True).start()

    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")

    try:
        while True:
            try:
                linea = input(f"{MI_ID} > ").strip()
            except EOFError:
                break

            if not linea:
                continue

            cmd = linea.split(' ', 2)
            comando = cmd[0].lower()

            if comando == 'salir':
                break

            elif comando == 'local':
                v_antes = list(reloj_vector)
                log_evento("LOCAL", "Evento interno", v_antes, tick_local())

            elif comando == 'enviar':
                if len(cmd) < 3:
                    print("[ERROR] Uso: enviar <PC_DESTINO> <MENSAJE>")
                    continue

                destino = cmd[1].upper()

                # FIX 2: evitar enviarse a uno mismo
                if destino == MI_ID:
                    print(f"[ERROR] No puedes enviarte un mensaje a ti mismo ({MI_ID}).")
                    continue

                if destino not in TABLA_RED:
                    print(f"[ERROR] '{destino}' no está activo. Nodos disponibles: {list(TABLA_RED.keys())}")
                    continue

                v_antes = list(reloj_vector)
                v_envio = tick_envio()
                paquete = {"origen": MI_ID, "vector": v_envio, "mensaje": cmd[2]}

                try:
                    sock.sendto(json.dumps(paquete).encode('utf-8'), TABLA_RED[destino])
                    log_evento("ENVÍO", f"Mensaje enviado a {destino} (UDP)", v_antes, v_envio)
                except Exception as e:
                    print(f"[ERROR] No se pudo enviar a {destino}: {e}")

            else:
                print(f"[ERROR] Comando desconocido: '{cmd[0]}'")
                print("        Comandos válidos: local | enviar <PC> <mensaje> | salir")

    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

    print("\n[INFO] Nodo detenido.")


if __name__ == "__main__":
    main()