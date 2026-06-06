import random
import socket
import sys
import threading
import time

# ============================================================================== 
# CONFIGURACION DE RED LAN
# ==============================================================================
NODOS = {
    "PC1": "192.168.1.10",
    "PC2": "192.168.1.11",
    "PC3": "192.168.1.12",
}

PUERTO = 7005

def obtener_nombre_nodo() -> str:
    if "--nombre" in sys.argv:
        indice = sys.argv.index("--nombre")
        if indice + 1 < len(sys.argv):
            return sys.argv[indice + 1]
    return "PC3"


MI_NOMBRE = obtener_nombre_nodo()

if MI_NOMBRE not in NODOS:
    raise ValueError(f"Nodo no valido: {MI_NOMBRE}. Usa uno de: {', '.join(NODOS)}")

MI_IP = NODOS[MI_NOMBRE]

MENSAJES = [
    "Revisando el estado del sistema",
    "Confirmo recepcion del evento",
    "Enviando actualizacion de la cola",
    "Proceso interno completado",
    "Sincronizando actividad distribuida",
    "Nuevo mensaje en el chat distribuido",
    "Registro de evento causal actualizado",
    "Lamport mantiene el orden de llegada",
]

INTERVALO_ENVIO_MIN = 2
INTERVALO_ENVIO_MAX = 5
TIEMPO_ESPERA_CONEXION = 3

reloj_logico = 0
lock = threading.Lock()
detener = threading.Event()


def obtener_nombre_por_ip(ip: str) -> str:
    for nombre, direccion in NODOS.items():
        if direccion == ip:
            return nombre
    return ip


def formatear_evento(reloj: int, tipo_evento: str, detalle: str) -> str:
    return f"[{reloj:04d}] {tipo_evento}: {detalle}"


def recibir_conexion(conexion: socket.socket, direccion_remota):
    global reloj_logico

    try:
        with conexion.makefile("r", encoding="utf-8") as flujo:
            linea = flujo.readline().strip()
            if not linea:
                return

            partes = linea.split("|", 1)
            if len(partes) != 2:
                return

            reloj_recibido = int(partes[0])
            texto = partes[1]
            origen = obtener_nombre_por_ip(direccion_remota[0])

            with lock:
                reloj_antes = reloj_logico
                reloj_logico = max(reloj_logico, reloj_recibido) + 1
                reloj_despues = reloj_logico

            print()
            print("=" * 70)
            print(formatear_evento(reloj_despues, "RECEPCION", f"desde {origen}"))
            print(f"Texto: {texto}")
            print(f"Reloj recibido: {reloj_recibido}")
            print(f"Mi reloj antes:  {reloj_antes}")
            print(f"Mi reloj despues: {reloj_despues}")
            print("=" * 70)
            print()

    except Exception as error:
        print(f"[-] Error al procesar una conexion entrante: {error}")
    finally:
        try:
            conexion.close()
        except OSError:
            pass


def servidor_tcp():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((MI_IP, PUERTO))
    servidor.listen()
    servidor.settimeout(1.0)

    print(f"[*] Nodo Lamport activo en {MI_IP}:{PUERTO}")
    print("[*] Esperando mensajes TCP de otros nodos...\n")

    while not detener.is_set():
        try:
            conexion, direccion_remota = servidor.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        hilo = threading.Thread(
            target=recibir_conexion,
            args=(conexion, direccion_remota),
            daemon=True,
        )
        hilo.start()

    try:
        servidor.close()
    except OSError:
        pass


def seleccionar_destino() -> str:
    destinos = [nombre for nombre in NODOS if nombre != MI_NOMBRE]
    return random.choice(destinos)


def seleccionar_texto() -> str:
    sufijo = random.randint(1, 999)
    return f"{random.choice(MENSAJES)} #{sufijo}"


def enviar_mensaje(destino: str, texto: str):
    global reloj_logico

    ip_destino = NODOS[destino]

    with lock:
        reloj_logico += 1
        reloj_envio = reloj_logico

    payload = f"{reloj_envio}|{texto}\n"

    try:
        with socket.create_connection((ip_destino, PUERTO), timeout=TIEMPO_ESPERA_CONEXION) as conexion:
            conexion.sendall(payload.encode("utf-8"))
    except OSError as error:
        print(f"[-] No se pudo enviar a {destino} ({ip_destino}): {error}")
        return

    print(formatear_evento(reloj_envio, "ENVIO", f"a {destino} -> {texto}"))


def bucle_envio_automatico():
    print("[*] Envio automatico activado.")
    print("[*] Cada mensaje incrementa el reloj local antes de salir y aplica Lamport al recibir.\n")

    while not detener.is_set():
        espera = random.uniform(INTERVALO_ENVIO_MIN, INTERVALO_ENVIO_MAX)
        if detener.wait(espera):
            break

        destino = seleccionar_destino()
        texto = seleccionar_texto()
        enviar_mensaje(destino, texto)


def main():
    print("-" * 72)
    print("   FASE 4 - RELOJES LOGICOS DE LAMPORT")
    print("-" * 72)
    print(f"Nodo activo: {MI_NOMBRE} | IP: {MI_IP} | Puerto TCP: {PUERTO}")
    print(f"Reloj inicial: L = {reloj_logico}")
    print("-" * 72)

    hilo_servidor = threading.Thread(target=servidor_tcp, daemon=True)
    hilo_servidor.start()

    try:
        bucle_envio_automatico()
    except KeyboardInterrupt:
        print("\n[*] Deteniendo nodo Lamport...")
    finally:
        detener.set()
        time.sleep(0.5)


if __name__ == "__main__":
    main()