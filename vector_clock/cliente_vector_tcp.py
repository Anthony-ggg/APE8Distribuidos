#!/usr/bin/env python3
"""
=============================================================
RELOJES DE VECTORES (Vector Clocks) - P2P TCP (5 POSICIONES)
=============================================================
Uso: python3 vector_clock_tcp.py --nombre PC1
"""

import socket
import threading
import json
import sys

# ── Tabla de red ──────────────────────────────────────────────────────────────
NODOS = {
    "PC1": ("192.168.1.10", 9001),
    "PC2": ("192.168.1.11", 9002),
    "PC3": ("192.168.1.12", 9003),
    # "PC4": ("192.168.1.13", 9004),
    # "PC5": ("192.168.1.14", 9005),
}

INDICE_NODO = {"PC1": 0, "PC2": 1, "PC3": 2, "PC4": 3, "PC5": 4}

# ── Identidad ─────────────────────────────────────────────────────────────────
if "--nombre" not in sys.argv:
    print("[ERROR] Debes indicar tu nodo con: python3 vector_clock_tcp.py --nombre PC1")
    print("        Valores válidos:", list(NODOS.keys()))
    sys.exit(1)

MI_NOMBRE = sys.argv[sys.argv.index("--nombre") + 1].upper()

if MI_NOMBRE not in NODOS:
    print(f"[ERROR] Nodo inválido: '{MI_NOMBRE}'. Válidos: {list(NODOS.keys())}")
    sys.exit(1)

MI_IP, MI_PUERTO = NODOS[MI_NOMBRE]
MI_INDICE        = INDICE_NODO[MI_NOMBRE]

reloj_vector = [0, 0, 0, 0, 0]
lock = threading.Lock()

# ── Utilidades ────────────────────────────────────────────────────────────────
def nombre_por_ip(ip: str) -> str:
    for nombre, (direccion, _) in NODOS.items():
        if direccion == ip:
            return nombre
    return ip

def log_evento(tipo, descripcion, v_antes, v_despues):
    print(f"\n  {'─'*60}")
    print(f"  EVENTO: {tipo} en {MI_NOMBRE}")
    print(f"  Descripción: {descripcion}")
    print(f"  Vector ANTES:   {v_antes}")
    print(f"  Vector DESPUÉS: {v_despues}")
    print(f"  {'─'*60}", flush=True)
    print(f"{MI_NOMBRE} > ", end="", flush=True)

# ── Servidor TCP (hilo en segundo plano) ──────────────────────────────────────
def manejar_cliente_tcp(conn, addr):
    try:
        fragmentos = []
        while True:
            parte = conn.recv(4096)
            if not parte:
                break
            fragmentos.append(parte)
        data = b"".join(fragmentos).decode("utf-8")
        if not data:
            return

        paquete = json.loads(data)
        origen  = nombre_por_ip(addr[0])

        with lock:
            v_antes = list(reloj_vector)
            vr = list(paquete["vector"]) + [0] * (5 - len(paquete["vector"]))
            for i in range(5):
                reloj_vector[i] = max(reloj_vector[i], vr[i])
            reloj_vector[MI_INDICE] += 1
            v_despues = list(reloj_vector)

        log_evento(
            "RECEPCIÓN",
            f"Desde {origen} via TCP: '{paquete['mensaje']}'",
            v_antes,
            v_despues,
        )
    except Exception as e:
        print(f"[WARN] Error procesando mensaje entrante: {e}")
    finally:
        conn.close()

def servidor_tcp():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", MI_PUERTO))
    srv.listen(10)
    print(f"  [TCP] Servidor escuchando en 0.0.0.0:{MI_PUERTO}\n")
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(
                target=manejar_cliente_tcp, args=(conn, addr), daemon=True
            ).start()
        except Exception as e:
            print(f"[WARN] Error en accept: {e}")

# ── Envío TCP ─────────────────────────────────────────────────────────────────
def enviar_tcp(destino: str, mensaje: str):
    if destino == MI_NOMBRE:
        print("[ERROR] No puedes enviarte un mensaje a ti mismo.")
        return

    with lock:
        reloj_vector[MI_INDICE] += 1
        v_envio = list(reloj_vector)
        v_antes = list(reloj_vector)
        v_antes[MI_INDICE] -= 1

    paquete = {"origen": MI_NOMBRE, "vector": v_envio, "mensaje": mensaje}
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.settimeout(5)
        cliente.connect(NODOS[destino])
        cliente.sendall(json.dumps(paquete).encode("utf-8"))
        cliente.shutdown(socket.SHUT_WR)
        cliente.close()
        log_evento("ENVÍO", f"Mensaje enviado a {destino} (TCP)", v_antes, v_envio)
    except socket.timeout:
        print(f"[ERROR] Tiempo de espera agotado al conectar a {destino}.")
    except ConnectionRefusedError:
        print(f"[ERROR] {destino} rechazó la conexión. ¿Está corriendo el script en esa PC?")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a {destino}: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"  RELOJES DE VECTORES TCP — NODO {MI_NOMBRE}")
    print("=" * 60)
    print(f"  IP: {MI_IP}  |  Puerto: {MI_PUERTO}  |  Índice: {MI_INDICE}")
    print(f"  Vector inicial : {reloj_vector}")
    print(f"  Nodos activos  : {list(NODOS.keys())}")
    print("=" * 60)

    threading.Thread(target=servidor_tcp, daemon=True).start()

    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")

    try:
        while True:
            try:
                linea = input(f"{MI_NOMBRE} > ").strip()
            except EOFError:
                break

            if not linea:
                continue

            cmd     = linea.split(" ", 2)
            comando = cmd[0].lower()

            if comando == "salir":
                break

            elif comando == "local":
                with lock:
                    v_antes = list(reloj_vector)
                    reloj_vector[MI_INDICE] += 1
                    v_despues = list(reloj_vector)
                log_evento("LOCAL", "Evento interno", v_antes, v_despues)

            elif comando == "enviar":
                if len(cmd) < 3:
                    print("[ERROR] Uso: enviar <PC_DESTINO> <mensaje>")
                    continue
                destino = cmd[1].upper()
                if destino not in NODOS:
                    print(f"[ERROR] '{destino}' no existe. Nodos: {list(NODOS.keys())}")
                    continue
                enviar_tcp(destino, cmd[2])

            else:
                print(f"[ERROR] Comando desconocido: '{cmd[0]}'")
                print("        Válidos: local | enviar <PC> <mensaje> | salir")

    except KeyboardInterrupt:
        pass

    print("\n[INFO] Nodo detenido.")

if __name__ == "__main__":
    main()