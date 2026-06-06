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
PUERTO = 8020

def obtener_nombre_nodo() -> str:
    if "--nombre" in sys.argv:
        indice = sys.argv.index("--nombre")
        if indice + 1 < len(sys.argv):
            return sys.argv[indice + 1]
    return "PC2"

MI_NOMBRE = obtener_nombre_nodo()
if MI_NOMBRE not in NODOS:
    raise ValueError(f"Nodo inválido: {MI_NOMBRE}. Usa uno de: {', '.join(NODOS)}")

MI_IP     = NODOS[MI_NOMBRE]
MI_INDICE = INDICE_NODO[MI_NOMBRE]

vector_tiempo = [0, 0, 0, 0, 0]
lock = threading.Lock()

def obtener_nombre_por_ip(ip: str) -> str:
    for nombre, direccion in NODOS.items():
        if direccion == ip:
            return nombre
    return ip

# ==============================================================================
# SERVIDOR UDP (hilo en segundo plano)
# ==============================================================================
def servidor_udp(sock):
    global vector_tiempo
    print(f"[*] Servidor UDP activo en puerto {PUERTO}...")

    while True:
        try:
            data, direccion_remota = sock.recvfrom(2048)
            linea = data.decode("utf-8").strip()
            if not linea:
                continue

            paquete = json.loads(linea)
            vector_recibido = paquete["vector"]
            texto  = paquete["texto"]
            origen = obtener_nombre_por_ip(direccion_remota[0])

            with lock:
                vector_antes = list(vector_tiempo)
                # REGLA DE RECEPCIÓN: W[i] = max(W[i], V[i])
                for i in range(5):
                    vector_tiempo[i] = max(vector_tiempo[i], vector_recibido[i])
                # Incrementa su propia posición después de combinar
                vector_tiempo[MI_INDICE] += 1
                vector_despues = list(vector_tiempo)

            print("\n" + "=" * 70)
            print(f"RECEPCION de {origen}")
            print(f"Texto: {texto}")
            print(f"Vector recibido:   {vector_recibido}")
            print(f"Mi vector antes:   {vector_antes}")
            print(f"Mi vector despues: {vector_despues}")
            print("=" * 70)
            print(f"{MI_NOMBRE} > ", end="", flush=True)

        except socket.timeout:
            continue
        except OSError:
            break
        except Exception as error:
            print(f"[-] Error en recepcion: {error}")

# ==============================================================================
# ENVÍO
# ==============================================================================
def enviar_mensaje_vector(sock, destino: str, texto: str):
    global vector_tiempo

    if destino == MI_NOMBRE:
        print("[-] No puedes enviarte un mensaje a ti mismo.")
        return

    ip_destino = NODOS[destino]

    with lock:
        # REGLA DE ENVÍO: Incrementar mi propia posición antes de salir
        vector_tiempo[MI_INDICE] += 1
        vector_envio = list(vector_tiempo)

    paquete = {"vector": vector_envio, "texto": texto}
    try:
        sock.sendto(json.dumps(paquete).encode("utf-8"), (ip_destino, PUERTO))
        print("\n" + "=" * 70)
        print(f"ENVIO a {destino}")
        print(f"Texto: {texto}")
        print(f"Vector enviado: {vector_envio}")
        print("=" * 70)
    except OSError as error:
        print(f"[-] No se pudo enviar a {destino}: {error}")

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("-" * 72)
    print("   VECTORES DE TIEMPO UDP — MENSAJES MANUALES")
    print("-" * 72)
    print(f"Nodo activo: {MI_NOMBRE} | IP: {MI_IP} | Índice Vector: {MI_INDICE}")
    print(f"Vector Inicial: {vector_tiempo}")
    print("-" * 72)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PUERTO))
    sock.settimeout(1.0)

    threading.Thread(target=servidor_udp, args=(sock,), daemon=True).start()

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
                    vector_antes = list(vector_tiempo)
                    vector_tiempo[MI_INDICE] += 1
                    vector_despues = list(vector_tiempo)
                print("\n" + "=" * 70)
                print(f"EVENTO LOCAL en {MI_NOMBRE}")
                print(f"Vector antes:   {vector_antes}")
                print(f"Vector despues: {vector_despues}")
                print("=" * 70)

            elif comando == "enviar":
                if len(cmd) < 3:
                    print("[ERROR] Uso: enviar <PC_DESTINO> <mensaje>")
                    continue
                destino = cmd[1].upper()
                if destino not in NODOS:
                    print(f"[ERROR] '{destino}' no existe. Nodos: {list(NODOS.keys())}")
                    continue
                enviar_mensaje_vector(sock, destino, cmd[2])

            else:
                print(f"[ERROR] Comando desconocido: '{cmd[0]}'")
                print("        Válidos: local | enviar <PC> <mensaje> | salir")

    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

    print("\n[*] Nodo detenido.")

if __name__ == "__main__":
    main()