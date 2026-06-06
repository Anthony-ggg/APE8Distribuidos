import socket
import sys
import threading
import json

# ==============================================================================
# CONFIGURACION DE RED LAN
# ==============================================================================
NODOS = {
    "PC1": "192.168.1.10",
    "PC2": "192.168.1.11",
    "PC3": "192.168.1.12",
    #"PC4": "192.168.1.13",
    #"PC5": "192.168.1.14"
}

INDICE_NODO = {"PC1": 0, "PC2": 1, "PC3": 2, "PC4": 3, "PC5": 4}
PUERTO = 7020

# ==============================================================================
# IDENTIDAD DEL NODO
# ==============================================================================
if "--nombre" not in sys.argv:
    print("[ERROR] Debes indicar tu nodo con: python3 script.py --nombre PC1")
    print("        Valores válidos:", list(NODOS.keys()))
    sys.exit(1)

MI_NOMBRE = sys.argv[sys.argv.index("--nombre") + 1].upper()

if MI_NOMBRE not in NODOS:
    print(f"[ERROR] Nodo inválido: '{MI_NOMBRE}'. Válidos: {list(NODOS.keys())}")
    sys.exit(1)

MI_IP     = NODOS[MI_NOMBRE]
MI_INDICE = INDICE_NODO[MI_NOMBRE]

vector_tiempo = [0, 0, 0, 0, 0]
lock = threading.Lock()

# ==============================================================================
# UTILIDADES
# ==============================================================================
def obtener_nombre_por_ip(ip: str) -> str:
    for nombre, direccion in NODOS.items():
        if direccion == ip:
            return nombre
    return ip

# ==============================================================================
# SERVIDOR UDP (hilo en segundo plano)
# ==============================================================================
def servidor_udp():
    global vector_tiempo
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(("0.0.0.0", PUERTO))
    srv.settimeout(1.0)
    print(f"  [UDP] Servidor escuchando en 0.0.0.0:{PUERTO}\n")

    while True:
        try:
            data, addr = srv.recvfrom(2048)
            paquete = json.loads(data.decode("utf-8").strip())
            vector_recibido = paquete["vector"]
            texto  = paquete["texto"]
            origen = obtener_nombre_por_ip(addr[0])

            with lock:
                v_antes = list(vector_tiempo)
                # Rellenar por si el vector recibido tiene menos de 5 posiciones
                vr = list(vector_recibido) + [0] * (5 - len(vector_recibido))
                for i in range(5):
                    vector_tiempo[i] = max(vector_tiempo[i], vr[i])
                vector_tiempo[MI_INDICE] += 1
                v_despues = list(vector_tiempo)

            print(f"\n  {'─'*60}")
            print(f"  EVENTO: RECEPCIÓN en {MI_NOMBRE}")
            print(f"  Descripción: Desde {origen}: '{texto}'")
            print(f"  Vector recibido : {vector_recibido}")
            print(f"  Vector ANTES    : {v_antes}")
            print(f"  Vector DESPUÉS  : {v_despues}")
            print(f"  {'─'*60}")
            print(f"{MI_NOMBRE} > ", end="", flush=True)

        except socket.timeout:
            continue
        except Exception as e:
            print(f"[WARN] Error en recepción: {e}")

# ==============================================================================
# ENVÍO MANUAL
# ==============================================================================
def enviar_mensaje(destino: str, texto: str):
    global vector_tiempo

    if destino == MI_NOMBRE:
        print(f"[ERROR] No puedes enviarte un mensaje a ti mismo.")
        return

    with lock:
        vector_tiempo[MI_INDICE] += 1
        v_envio = list(vector_tiempo)

    paquete = {"vector": v_envio, "texto": texto}

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cliente.sendto(json.dumps(paquete).encode("utf-8"), (NODOS[destino], PUERTO))
        cliente.close()
        print(f"\n  {'─'*60}")
        print(f"  EVENTO: ENVÍO desde {MI_NOMBRE}")
        print(f"  Descripción: Mensaje enviado a {destino}: '{texto}'")
        print(f"  Vector DESPUÉS  : {v_envio}")
        print(f"  {'─'*60}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar a {destino}: {e}")

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("=" * 60)
    print(f"  FASE 5 - VECTORES DE TIEMPO — NODO {MI_NOMBRE}")
    print("=" * 60)
    print(f"  IP: {MI_IP}  |  Puerto: {PUERTO}  |  Índice: {MI_INDICE}")
    print(f"  Vector inicial : {vector_tiempo}")
    print(f"  Nodos activos  : {list(NODOS.keys())}")
    print("=" * 60)

    threading.Thread(target=servidor_udp, daemon=True).start()

    print("\n[COMANDOS]: local | enviar <PC> <mensaje> | salir\n")

    try:
        while True:
            try:
                linea = input(f"{MI_NOMBRE} > ").strip()
            except EOFError:
                break

            if not linea:
                continue

            cmd = linea.split(" ", 2)
            comando = cmd[0].lower()

            if comando == "salir":
                break

            elif comando == "local":
                with lock:
                    v_antes = list(vector_tiempo)
                    vector_tiempo[MI_INDICE] += 1
                    v_despues = list(vector_tiempo)
                print(f"\n  {'─'*60}")
                print(f"  EVENTO: LOCAL en {MI_NOMBRE}")
                print(f"  Vector ANTES    : {v_antes}")
                print(f"  Vector DESPUÉS  : {v_despues}")
                print(f"  {'─'*60}")

            elif comando == "enviar":
                if len(cmd) < 3:
                    print("[ERROR] Uso: enviar <PC_DESTINO> <mensaje>")
                    continue
                destino = cmd[1].upper()
                if destino not in NODOS:
                    print(f"[ERROR] '{destino}' no existe. Nodos: {list(NODOS.keys())}")
                    continue
                enviar_mensaje(destino, cmd[2])

            else:
                print(f"[ERROR] Comando desconocido: '{cmd[0]}'")
                print("        Válidos: local | enviar <PC> <mensaje> | salir")

    except KeyboardInterrupt:
        pass

    print("\n[INFO] Nodo detenido.")

if __name__ == "__main__":
    main()