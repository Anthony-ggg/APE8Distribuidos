import random
import socket
import sys
import threading
import time
import json

# ============================================================================== 
# CONFIGURACION DE RED LAN (Fase 1 de la Guía)
# ==============================================================================
NODOS = {
    "PC1": "192.168.1.10",
    "PC2": "192.168.1.11",
    "PC3": "192.168.1.12",
    "PC4": "192.168.1.13",
    "PC5": "192.168.1.14"
}

# Mapeo estático de nombres a índices del vector [0, 1, 2, 3, 4]
INDICE_NODO = {"PC1": 0, "PC2": 1, "PC3": 2, "PC4": 3, "PC5": 4}
PUERTO = 7020

def obtener_nombre_nodo() -> str:
    if "--nombre" in sys.argv:
        indice = sys.argv.index("--nombre")
        if indice + 1 < len(sys.argv):
            return sys.argv[indice + 1]
    return "PC1"

MI_NOMBRE = obtener_nombre_nodo()
if MI_NOMBRE not in NODOS:
    raise ValueError(f"Nodo inválido: {MI_NOMBRE}. Usa uno de: {', '.join(NODOS)}")

MI_IP = NODOS[MI_NOMBRE]
MI_INDICE = INDICE_NODO[MI_NOMBRE]

MENSAJES = [
    "Actualizando estado del cluster",
    "Transaccion causal iniciada",
    "Escritura en base de datos local",
    "Evento concurrente generado",
    "Sincronizando hilos del vector",
]

INTERVALO_ENVIO_MIN = 3
INTERVALO_ENVIO_MAX = 6

# Inicialización del Vector de Tiempo de 5 posiciones [0, 0, 0, 0, 0]
vector_tiempo = [0, 0, 0, 0, 0]
lock = threading.Lock()
detener = threading.Event()

def obtener_nombre_por_ip(ip: str) -> str:
    for nombre, direccion in NODOS.items():
        if direccion == ip:
            return nombre
    return ip

def servidor_udp():
    global vector_tiempo
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind(("0.0.0.0", PUERTO))  # Escucha en todas las interfaces para evitar Errno 99
    servidor.settimeout(1.0)

    print(f"[*] Servidor de Vectores activo en puerto {PUERTO}...")
    
    while not detener.is_set():
        try:
            data, direccion_remota = servidor.recvfrom(2048)
            linea = data.decode("utf-8").strip()
            if not linea:
                continue

            # El mensaje viaja como JSON: {"vector": [...], "texto": "...", "origen": "..."}
            paquete = json.loads(linea)
            vector_recibido = paquete["vector"]
            texto = paquete["texto"]
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
            print(f"Vector recibido: {vector_recibido}")
            print(f"Mi vector antes:  {vector_antes}")
            print(f"Mi vector despues: {vector_despues}")
            print("=" * 70 + "\n")

        except socket.timeout:
            continue
        except Exception as error:
            print(f"[-] Error en recepcion: {error}")
            continue

    servidor.close()

def enviar_mensaje_vector(destino: str, texto: str):
    global vector_tiempo
    ip_destino = NODOS[destino]

    with lock:
        # REGLA DE ENVÍO: Incrementar mi propia posición antes de salir
        vector_tiempo[MI_INDICE] += 1
        vector_envio = list(vector_tiempo)

    # Construimos el payload estructurado
    paquete = {
        "vector": vector_envio,
        "texto": texto
    }
    payload = json.dumps(paquete)

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cliente.sendto(payload.encode("utf-8"), (ip_destino, PUERTO))
        print(f"[{vector_envio}] ENVIO a {destino} -> {texto}")
    except OSError as error:
        print(f"[-] No se pudo enviar a {destino}: {error}")

def bucle_envio_automatico():
    destinos = [nombre for nombre in NODOS if nombre != MI_NOMBRE]
    print("[*] Envío automático activado.\n")

    while not detener.is_set():
        espera = random.uniform(INTERVALO_ENVIO_MIN, INTERVALO_ENVIO_MAX)
        if detener.wait(espera):
            break

        destino = random.choice(destinos)
        texto = f"{random.choice(MENSAJES)} #{random.randint(1, 999)}"
        enviar_mensaje_vector(destino, texto)

def main():
    print("-" * 72)
    print("   FASE 5 - VECTORES DE TIEMPO (5 NODOS LAN)")
    print("-" * 72)
    print(f"Nodo activo: {MI_NOMBRE} | IP: {MI_IP} | Índice Vector: {MI_INDICE}")
    print(f"Vector Inicial: {vector_tiempo}")
    print("-" * 72)

    hilo_servidor = threading.Thread(target=servidor_udp, daemon=True)
    hilo_servidor.start()

    try:
        bucle_envio_automatico()
    except KeyboardInterrupt:
        print("\n[*] Deteniendo nodo...")
    finally:
        detener.set()
        time.sleep(0.5)

if __name__ == "__main__":
    main()