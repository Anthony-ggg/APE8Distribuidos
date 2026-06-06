import random
import socket
import sys
import threading
import time

# ============================================================================== 
# CONFIGURACION DE RED LAN (Fase 1 de la Guía)
# ==============================================================================
NODOS = {
    "PC1": "192.168.1.10",
    "PC2": "192.168.1.11",
    "PC3": "192.168.1.12"
}

PUERTO = 7010 # Cambiado levemente el puerto para evitar colisiones si corren juntos

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

def servidor_udp():
    global reloj_logico
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind((MI_IP, PUERTO))
    servidor.settimeout(1.0)

    print(f"[*] Nodo Lamport UDP activo en {MI_IP}:{PUERTO}")
    print("[*] Esperando mensajes UDP de otros nodos...\n")

    while not detener.is_set():
        try:
            # En UDP recibimos directamente el buffer completo del paquete
            data, direccion_remota = servidor.recvfrom(2048)
            linea = data.decode("utf-8").strip()
            if not linea:
                continue

            partes = linea.split("|", 1)
            if len(partes) != 2:
                continue

            reloj_recibido = int(partes[0])
            texto = partes[1]
            origen = obtener_nombre_por_ip(direccion_remota[0])

            with lock:
                reloj_antes = reloj_logico
                # REGLA DE RECEPCIÓN LAMPORT
                reloj_logico = max(reloj_logico, reloj_recibido) + 1
                reloj_despues = reloj_logico

            print("\n" + "=" * 70)
            print(formatear_evento(reloj_despues, "RECEPCION UDP", f"desde {origen}"))
            print(f"Texto: {texto}")
            print(f"Reloj recibido: {reloj_recibido}")
            print(f"Mi reloj antes:  {reloj_antes}")
            print(f"Mi reloj despues: {reloj_despues}")
            print("=" * 70 + "\n")

        except socket.timeout:
            continue
        except OSError:
            break

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

def enviar_mensaje_udp(destino: str, texto: str):
    global reloj_logico
    ip_destino = NODOS[destino]

    with lock:
        # REGLA DE ENVÍO LAMPORT
        reloj_logico += 1
        reloj_envio = reloj_logico

    payload = f"{reloj_envio}|{texto}\n"

    try:
        # En UDP no creamos conexiones estables, enviamos directo a la IP y puerto
        cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cliente.sendto(payload.encode("utf-8"), (ip_destino, PUERTO))
    except OSError as error:
        print(f"[-] No se pudo enviar por UDP a {destino} ({ip_destino}): {error}")
        return

    print(formatear_evento(reloj_envio, "ENVIO UDP", f"a {destino} -> {texto}"))

def bucle_envio_automatico():
    print("[*] Envio automatico activado.")
    print("[*] Cada mensaje incrementa el reloj local antes de salir.\n")

    while not detener.is_set():
        espera = random.uniform(INTERVALO_ENVIO_MIN, INTERVALO_ENVIO_MAX)
        if detener.wait(espera):
            break

        destino = seleccionar_destino()
        texto = seleccionar_texto()
        enviar_mensaje_udp(destino, texto)

def main():
    print("-" * 72)
    print("   FASE 4 - RELOJES LOGICOS DE LAMPORT (UDP)")
    print("-" * 72)
    print(f"Nodo activo: {MI_NOMBRE} | IP: {MI_IP} | Puerto UDP: {PUERTO}")
    print(f"Reloj inicial: L = {reloj_logico}")
    print("-" * 72)

    hilo_servidor = threading.Thread(target=servidor_udp, daemon=True)
    hilo_servidor.start()

    try:
        bucle_envio_automatico()
    except KeyboardInterrupt:
        print("\n[*] Deteniendo nodo Lamport UDP...")
    finally:
        detener.set()
        time.sleep(0.5)

if __name__ == "__main__":
    main()